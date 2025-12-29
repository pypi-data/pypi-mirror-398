CRUD_TEMPLATE = """\
    from datetime import datetime
from typing import Type, Dict, Any, List
from sqlmodel import SQLModel, Session, select, text


# -------------------------------
# Response Utilities
# -------------------------------
class ResponseUtils:
    class getLogLevel:
        ERROR = "ERROR"

    @staticmethod
    def responseWithData(success, code, message, data, **optional):
        return {
            "status": success,
            "status_code": code,
            "message": message,
            "data": data,
        }

    @staticmethod
    def responseWithoutData(success, code, message, **optional):
        return {"status": success, "status_code": code, "message": message}

    @staticmethod
    def logger(name, level, message):
        print(f"[{level}] {name}: {message}")


AppUtils = ResponseUtils


# -------------------------------
# CRUD Class
# -------------------------------
class CRUD:
    @staticmethod
    def create(session: Session, model: Type[SQLModel], data):
        try:
            # Convert model to dict
            if hasattr(data, "model_dump"):
                data = data.model_dump(exclude_unset=True)
            elif hasattr(data, "dict"):
                data = data.dict(exclude_unset=True)

            # Create object
            new_obj = model(**data)

            # 🔥 BUILD INSERT STATEMENT
            # insert_stmt = model.__table__.insert().values(**data)

            # # 🔥 COMPILE TO RAW SQL (PostgreSQL)
            # compiled_sql = insert_stmt.compile(
            #     dialect=postgresql.dialect(),
            #     compile_kwargs={"literal_binds": True},
            # )

            # # ✅ PRINT INSERT SCRIPT
            # print("🔹 INSERT SCRIPT 🔹")
            # print(compiled_sql)

            # Execute insert
            session.add(new_obj)
            session.flush()  # no commit
            session.refresh(new_obj)

            return AppUtils.responseWithData(
                True, 200, "Record(s) Created successfully!", new_obj
            )

        except Exception as ex:
            raise ex

    # ---------- CREATE MULTIPLE ----------
    @staticmethod
    def create_multiple(
        session: Session, model: Type[SQLModel], data_list: List[Dict[str, Any]]
    ):
        try:
            new_objs = [model(**data) for data in data_list]
            session.add_all(new_objs)
            session.commit()
            for obj in new_objs:
                session.refresh(obj)
            return AppUtils.responseWithData(True, 200, "Created multiple", new_objs)
        except Exception as ex:
            raise ex

    # ---------- READ ----------

    @staticmethod
    def read(
        session: Session,
        model: Type[SQLModel],
        filters: Any = None,
        order_by: Any = None,
    ):
        try:
            stmt = select(model)

            # Apply filters if any
            if filters:
                for f in filters:
                    stmt = stmt.where(f)

            # Apply order_by (single or multiple)
            if order_by is not None:
                if isinstance(order_by, (list, tuple)):
                    stmt = stmt.order_by(*order_by)
                else:
                    stmt = stmt.order_by(order_by)

            # 🧩 Print the compiled SQL query
            compiled = stmt.compile(compile_kwargs={"literal_binds": True})
            print("🧩 Executed SQL:", compiled)

            return session.exec(stmt).all()

        except Exception as ex:
            raise ex

    # ---------- UPDATE ----------

    @staticmethod
    def update(session: Session, model: Type[SQLModel], data: Dict[str, Any]):
        try:
            # ✅ Convert pydantic/SQLModel to dict if needed
            if not isinstance(data, dict):
                if hasattr(data, "dict"):
                    data = data.dict(exclude_unset=True)
                else:
                    return AppUtils.responseWithoutData(
                        False, 400, "Data must be a dictionary"
                    )

            # Step 1: Find primary key
            pk_columns = [c for c in model.__table__.primary_key.columns]
            if not pk_columns:
                return AppUtils.responseWithoutData(
                    False, 400, "No primary key found in model"
                )

            pk_column = pk_columns[0]
            pk_name = pk_column.name

            # Step 2: Get primary key value
            obj_id = data.get(pk_name, None)
            if obj_id is None:
                return AppUtils.responseWithoutData(
                    False, 400, f"Primary key '{pk_name}' not found in data"
                )

            # Step 3: Remove PK from update payload
            update_data = {
                k: v for k, v in data.items() if k.lower() != pk_name.lower()
            }

            # Step 4: Fetch object
            stmt = select(model).where(getattr(model, pk_name) == obj_id)
            obj = session.exec(stmt).first()
            if not obj:
                return AppUtils.responseWithoutData(False, 404, "Object not found")

            # Step 5: Apply updates
            for k, v in update_data.items():
                if hasattr(obj, k):
                    setattr(obj, k, v)

            # Step 6: Auto-update timestamp
            if hasattr(obj, "updated_at"):
                setattr(obj, "updated_at", datetime.now())
            if hasattr(obj, "modified_at"):
                setattr(obj, "modified_at", datetime.now())
            # --------------------------------------------------------------
            from sqlalchemy import event
            from sqlalchemy.engine import Engine

            @event.listens_for(Engine, "before_cursor_execute")
            def before_cursor_execute(
                conn, cursor, statement, parameters, context, executemany
            ):
                if statement.strip().upper().startswith("UPDATE"):
                    print("\n🔥 SQL UPDATE QUERY 🔥")
                    print(statement)
                    print("🔥 PARAMETERS 🔥")
                    print(parameters)

            # --------------------------------------------------------------
            session.add(obj)
            session.flush()

            return AppUtils.responseWithData(
                True, 200, "Record(s) Updated successfully!", obj
            )

        except Exception as ex:
            raise ex

    @staticmethod
    def update_multiple(
        session: Session,
        model: Type[SQLModel],
        updates: List[Dict[str, Any]],
        id_field="id",
    ):
        try:
            updated_objs = []
            for upd in updates:
                obj_id = upd.get(id_field)
                stmt = select(model).where(getattr(model, id_field) == obj_id)
                obj = session.exec(stmt).first()
                if obj:
                    for k, v in upd.items():
                        if k != id_field:
                            setattr(obj, k, v)
                    session.add(obj)
                    updated_objs.append(obj)
            session.commit()
            for obj in updated_objs:
                session.refresh(obj)
            return AppUtils.responseWithData(
                True, 200, "Updated multiple", updated_objs
            )
        except Exception as ex:
            raise ex

    # ---------- DELETE ----------
    # ---------- DELETE ----------
    @staticmethod
    def delete(
        session: Session,
        model: Type[SQLModel],
        obj_id: Any = None,
        id_field: str = "id",
        filters: Any = None,
    ):
        try:
            stmt = select(model)

            # Case 1: Delete using filters
            if filters:
                for f in filters:
                    stmt = stmt.where(f)

                objects = session.exec(stmt).all()

                if not objects:
                    return AppUtils.responseWithoutData(False, 404, "No records found")

                for obj in objects:
                    session.delete(obj)

                session.commit()
                return AppUtils.responseWithoutData(True, 200, "Deleted successfully")

            # Case 2: Delete using primary key
            if obj_id is None:
                return AppUtils.responseWithoutData(False, 400, "obj_id is required")

            stmt = select(model).where(getattr(model, id_field) == obj_id)
            obj = session.exec(stmt).first()

            if not obj:
                return AppUtils.responseWithoutData(False, 404, "Object not found")

            session.delete(obj)
            session.commit()
            return AppUtils.responseWithoutData(True, 200, "Deleted successfully")

        except Exception as ex:
            raise ex

    # ---------- DELETE MULTIPLE ----------
    @staticmethod
    def delete_multiple(
        session: Session, model: Type[SQLModel], ids: List[Any], id_field="id"
    ):
        try:
            deleted_count = 0
            for obj_id in ids:
                stmt = select(model).where(getattr(model, id_field) == obj_id)
                obj = session.exec(stmt).first()
                if obj:
                    session.delete(obj)
                    deleted_count += 1
            session.commit()
            return AppUtils.responseWithData(
                True, 200, f"Deleted {deleted_count} records", deleted_count
            )
        except Exception as ex:
            raise ex

    @staticmethod
    def join_multi(
        session: Session,
        base_query,
        joins: list,
        filters: list = None,
        order_by=None,
        select_columns=None,
    ):
        try:
            # SELECT
            if select_columns:
                stmt = select(*select_columns)
            else:
                stmt = base_query

            # Apply joins
            for join_item in joins:
                model, condition, join_type = join_item

                if join_type == "inner":
                    stmt = stmt.join(model, condition)
                else:
                    stmt = stmt.join(model, condition, isouter=True)

            # Filters
            if filters:
                for f in filters:
                    stmt = stmt.where(f)

            # Order By
            if order_by:
                if isinstance(order_by, (list, tuple)):
                    stmt = stmt.order_by(*order_by)
                else:
                    stmt = stmt.order_by(order_by)

            # Debug SQL
            compiled = stmt.compile(compile_kwargs={"literal_binds": True})
            print("🧩 MULTI-JOIN SQL:", compiled)

            return session.exec(stmt).all()

        except Exception as ex:
            raise ex

    @staticmethod
    async def raw_sql(session: Session, query: str):
        try:
            stmt = text(query)
            compiled = stmt.compile(compile_kwargs={"literal_binds": True})
            print("🧩 RAW SQL:", compiled)

            result = await session.exec(stmt)
            return result.all()

        except Exception as ex:
            raise ex

    """
