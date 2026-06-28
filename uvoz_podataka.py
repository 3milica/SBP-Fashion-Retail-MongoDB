import csv
import pymongo
from dateutil import parser


class FashionRetailParser:

    def __init__(self, customers_file, products_file, stores_file,
                 employees_file, discounts_file, transactions_file):
        self._customers_file = customers_file
        self._products_file = products_file
        self._stores_file = stores_file
        self._employees_file = employees_file
        self._discounts_file = discounts_file
        self._transactions_file = transactions_file

        self._customers = {}
        self._products = {}
        self._stores = {}
        self._employees = {}

    def _load_customers(self):
        with open(self._customers_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = int(row["Customer ID"])
                self._customers[cid] = {
                    "customer_id": cid,
                    "name": row["Name"],
                    "city": row["City"],
                    "country": row["Country"],
                    "gender": row["Gender"],
                    "date_of_birth": row["Date Of Birth"],
                }

    def _load_products(self):
        with open(self._products_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = int(row["Product ID"])
                self._products[pid] = {
                    "product_id": pid,
                    "category": row["Category"],
                    "sub_category": row["Sub Category"],
                    "production_cost": float(row["Production Cost"]),
                }

    def _load_stores(self):
        with open(self._stores_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = int(row["Store ID"])
                self._stores[sid] = {
                    "store_id": sid,
                    "store_name": row["Store Name"],
                    "country": row["Country"],
                    "city": row["City"],
                }

    def _load_employees(self):
        with open(self._employees_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                eid = int(row["Employee ID"])
                self._employees[eid] = {
                    "employee_id": eid,
                    "name": row["Name"],
                    "position": row["Position"],
                    "store_id": int(row["Store ID"]),
                }

    def load_lookup_tables(self):
        self._load_customers()
        self._load_products()
        self._load_stores()
        self._load_employees()

    # ---------- Glavna kolekcija: transactions ----------

    def get_transaction(self, row: dict) -> dict:
        customer_id = int(row["Customer ID"])
        product_id = int(row["Product ID"])
        store_id = int(row["Store ID"])
        employee_id = int(row["Employee ID"])

        return {
            "invoice_id": row["Invoice ID"],
            "line": int(row["Line"]),
            "date": parser.parse(row["Date"]),
            "transaction_type": row["Transaction Type"],
            "payment_method": row["Payment Method"],
            "unit_price": float(row["Unit Price"]),
            "quantity": int(row["Quantity"]),
            "discount": float(row["Discount"]),
            "line_total": float(row["Line Total"]),
            "invoice_total": float(row["Invoice Total"]),
            "currency": row["Currency"],
            "currency_symbol": row["Currency Symbol"],
            "sku": row["SKU"],
            "size": row["Size"],
            "color": row["Color"],
            "customer": self._customers.get(customer_id, {"customer_id": customer_id}),
            "product": self._products.get(product_id, {"product_id": product_id}),
            "store": self._stores.get(store_id, {"store_id": store_id}),
            "employee": self._employees.get(employee_id, {"employee_id": employee_id}),
        }

    def add_all_transactions_to_db(self, url, db_name,
                                    collection_name="transactions",
                                    batch_size=5000):
        client = pymongo.MongoClient(url)
        db = client[db_name]

        db[collection_name].drop()  # obriši staru kolekciju da ne dupliraš

        batch = []
        count = 0

        with open(self._transactions_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                batch.append(self.get_transaction(row))
                count += 1

                if len(batch) >= batch_size:
                    db[collection_name].insert_many(batch)
                    batch = []
                    print(f"Uvezeno: {count} transakcija...")

        if batch:
            db[collection_name].insert_many(batch)

        print(f"Završeno. Ukupno uvezeno: {count} transakcija.")
        print(f"Kolekcija: {db_name}.{collection_name}")

    def add_discounts_to_db(self, url, db_name):
        client = pymongo.MongoClient(url)
        db = client[db_name]

        discounts = []
        with open(self._discounts_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                discounts.append({
                    "start_date": row["Start"],
                    "end_date": row["End"],
                    "discount": float(row["Discont"]),
                    "description": row["Description"],
                    "category": row["Category"],
                    "sub_category": row["Sub Category"],
                })

        if discounts:
            db["discounts"].insert_many(discounts)
        print(f"Uvezeno {len(discounts)} kampanja u discounts.")


if __name__ == "__main__":
    parser_obj = FashionRetailParser(
        customers_file="csv_files/customers.csv",
        products_file="csv_files/products.csv",
        stores_file="csv_files/stores.csv",
        employees_file="csv_files/employees.csv",
        discounts_file="csv_files/discounts.csv",
        transactions_file="csv_files/transactions.csv",
    )

    print("Učitavanje tabela (customers, products, stores, employees)...")
    parser_obj.load_lookup_tables()

    print("Uvoz SVIH transakcija u MongoDB...")
    parser_obj.add_all_transactions_to_db(
        "mongodb://localhost:27017",
        "fashion_retail",
        collection_name="transactions",
    )

    print("Uvoz discounts u MongoDB...")
    parser_obj.add_discounts_to_db("mongodb://localhost:27017", "fashion_retail")