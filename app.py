import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
from datetime import datetime

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="SmartStock",
    page_icon="📦",
    layout="wide"
)

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>
    .main-title {
        font-size: 34px;
        font-weight: 700;
        margin-bottom: 0;
    }

    .subtitle {
        color: #666;
        font-size: 16px;
        margin-bottom: 25px;
    }

    div[data-testid="stMetric"] {
        border: 1px solid #dddddd;
        padding: 15px;
        border-radius: 10px;
    }

    .section-title {
        font-size: 23px;
        font-weight: 600;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# MONGODB CONNECTION
# =========================================================
@st.cache_resource
def get_database():
    client = MongoClient(
        "mongodb://127.0.0.1:27018",
        serverSelectionTimeoutMS=5000
    )
    client.admin.command("ping")
    return client["smartstock_db"]

try:
    db = get_database()

    products = db["products"]
    sales = db["sales"]
    suppliers = db["suppliers"]
    stock_movements = db["stock_movements"]

except Exception as e:
    st.error("MongoDB connection failed.")
    st.code(str(e))
    st.stop()

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("📦 SmartStock")
st.sidebar.caption("Inventory & Sales Analytics")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "📦 Products & Inventory",
        "🧾 Sales Management",
        "🚚 Suppliers",
        "🔄 Stock Movements",
        "📊 Analytics"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("MongoDB Connected • Port 27018")

# =========================================================
# DASHBOARD
# =========================================================
if page == "🏠 Dashboard":

    st.markdown(
        '<p class="main-title">📦 SmartStock</p>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<p class="subtitle">Inventory & Sales Analytics System</p>',
        unsafe_allow_html=True
    )

    # Get data
    product_data = list(products.find({}, {"_id": 0}))
    sales_data = list(sales.find({}, {"_id": 0}))

    product_df = pd.DataFrame(product_data)
    sales_df = pd.DataFrame(sales_data)

    # Metrics
    total_products = products.count_documents({})
    total_sales_records = sales.count_documents({})
    total_suppliers = suppliers.count_documents({})
    total_movements = stock_movements.count_documents({})

    if not sales_df.empty and "total_amount" in sales_df.columns:
        total_revenue = sales_df["total_amount"].sum()
    else:
        total_revenue = 0

    if not product_df.empty and "quantity" in product_df.columns:
        total_stock = product_df["quantity"].sum()
    else:
        total_stock = 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("📦 Products", total_products)
    col2.metric("📊 Stock Units", int(total_stock))
    col3.metric("💰 Revenue", f"₹{total_revenue:,.0f}")
    col4.metric("🚚 Suppliers", total_suppliers)

    st.markdown("---")

    # Low stock
    st.subheader("⚠️ Low Stock Products")

    if not product_df.empty:
        low_stock = product_df[
            product_df["quantity"] <= product_df["reorder_level"]
        ]

        if not low_stock.empty:
            st.dataframe(
                low_stock,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("All products have sufficient stock.")

    # Recent sales
    st.subheader("🧾 Recent Sales")

    if not sales_df.empty:
        st.dataframe(
            sales_df.tail(10),
            use_container_width=True,
            hide_index=True
        )

# =========================================================
# PRODUCTS & INVENTORY
# =========================================================
elif page == "📦 Products & Inventory":

    st.title("📦 Products & Inventory")

    tab1, tab2, tab3 = st.tabs(
        ["View Products", "Add Product", "Edit / Delete"]
    )

    # -----------------------------------------------------
    # VIEW
    # -----------------------------------------------------
    with tab1:

        data = list(products.find({}, {"_id": 0}))

        if data:
            df = pd.DataFrame(data)

            search = st.text_input(
                "🔎 Search product",
                placeholder="Enter product name..."
            )

            if search:
                df = df[
                    df["product_name"]
                    .str.contains(search, case=False, na=False)
                ]

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No products found.")

    # -----------------------------------------------------
    # ADD
    # -----------------------------------------------------
    with tab2:

        st.subheader("Add New Product")

        with st.form("add_product"):

            name = st.text_input("Product Name")
            category = st.text_input("Category")
            price = st.number_input(
                "Price",
                min_value=0.0,
                step=1.0
            )
            quantity = st.number_input(
                "Quantity",
                min_value=0,
                step=1
            )
            supplier = st.text_input("Supplier")
            reorder = st.number_input(
                "Reorder Level",
                min_value=0,
                step=1
            )

            submitted = st.form_submit_button(
                "➕ Add Product"
            )

            if submitted:

                if not name:
                    st.error("Product name is required.")

                else:

                    products.insert_one({
                        "product_name": name,
                        "category": category,
                        "price": price,
                        "quantity": quantity,
                        "supplier": supplier,
                        "reorder_level": reorder
                    })

                    st.success(
                        f"{name} added successfully to MongoDB!"
                    )

                    st.rerun()

    # -----------------------------------------------------
    # EDIT / DELETE
    # -----------------------------------------------------
    with tab3:

        product_list = list(
            products.find({}, {"_id": 0})
        )

        if product_list:

            names = [
                p["product_name"]
                for p in product_list
            ]

            selected = st.selectbox(
                "Select Product",
                names
            )

            product = products.find_one(
                {"product_name": selected}
            )

            st.subheader("Edit Product")

            with st.form("edit_product"):

                new_price = st.number_input(
                    "Price",
                    value=float(product.get("price", 0))
                )

                new_quantity = st.number_input(
                    "Quantity",
                    value=int(product.get("quantity", 0))
                )

                new_supplier = st.text_input(
                    "Supplier",
                    value=product.get("supplier", "")
                )

                new_reorder = st.number_input(
                    "Reorder Level",
                    value=int(product.get("reorder_level", 0))
                )

                update = st.form_submit_button(
                    "💾 Update Product"
                )

                if update:

                    products.update_one(
                        {"product_name": selected},
                        {
                            "$set": {
                                "price": new_price,
                                "quantity": new_quantity,
                                "supplier": new_supplier,
                                "reorder_level": new_reorder
                            }
                        }
                    )

                    st.success("Product updated in MongoDB!")
                    st.rerun()

            st.markdown("---")

            if st.button(
                "🗑️ Delete Product",
                type="secondary"
            ):

                products.delete_one(
                    {"product_name": selected}
                )

                st.success(
                    "Product deleted from MongoDB!"
                )

                st.rerun()

# =========================================================
# SALES MANAGEMENT
# =========================================================
elif page == "🧾 Sales Management":

    st.title("🧾 Sales Management")

    tab1, tab2 = st.tabs(
        ["Sales Records", "Add Sale"]
    )

    # -----------------------------------------------------
    # SALES RECORDS
    # -----------------------------------------------------
    with tab1:

        data = list(
            sales.find({}, {"_id": 0})
        )

        if data:

            df = pd.DataFrame(data)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            if "total_amount" in df.columns:

                st.metric(
                    "Total Revenue",
                    f"₹{df['total_amount'].sum():,.2f}"
                )

        else:
            st.info("No sales records available.")

    # -----------------------------------------------------
    # ADD SALE
    # -----------------------------------------------------
    with tab2:

        st.subheader("Record New Sale")

        product_data = list(
            products.find({}, {"_id": 0})
        )

        if product_data:

            product_names = [
                p["product_name"]
                for p in product_data
            ]

            with st.form("add_sale"):

                selected_product = st.selectbox(
                    "Product",
                    product_names
                )

                quantity = st.number_input(
                    "Quantity Sold",
                    min_value=1,
                    step=1
                )

                customer = st.text_input(
                    "Customer"
                )

                sale_date = st.date_input(
                    "Sale Date"
                )

                submit_sale = st.form_submit_button(
                    "🧾 Record Sale"
                )

                if submit_sale:

                    product = products.find_one({
                        "product_name":
                        selected_product
                    })

                    if product["quantity"] < quantity:

                        st.error(
                            "Not enough stock available."
                        )

                    else:

                        unit_price = product["price"]

                        total = (
                            unit_price * quantity
                        )

                        sales.insert_one({
                            "product_name":
                            selected_product,

                            "quantity":
                            quantity,

                            "unit_price":
                            unit_price,

                            "total_amount":
                            total,

                            "sale_date":
                            str(sale_date),

                            "customer":
                            customer
                        })

                        # Reduce inventory
                        products.update_one(
                            {
                                "product_name":
                                selected_product
                            },
                            {
                                "$inc":
                                {
                                    "quantity":
                                    -quantity
                                }
                            }
                        )

                        # Add stock movement
                        stock_movements.insert_one({
                            "product_name":
                            selected_product,

                            "movement_type":
                            "OUT",

                            "quantity":
                            quantity,

                            "movement_date":
                            str(sale_date),

                            "supplier":
                            product.get(
                                "supplier",
                                ""
                            )
                        })

                        st.success(
                            "Sale recorded and inventory updated!"
                        )

                        st.rerun()

# =========================================================
# SUPPLIERS
# =========================================================
elif page == "🚚 Suppliers":

    st.title("🚚 Supplier Management")

    tab1, tab2 = st.tabs(
        ["Supplier List", "Add Supplier"]
    )

    with tab1:

        data = list(
            suppliers.find({}, {"_id": 0})
        )

        if data:

            df = pd.DataFrame(data)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info("No suppliers found.")

    with tab2:

        st.subheader("Add Supplier")

        with st.form("supplier_form"):

            name = st.text_input(
                "Supplier Name"
            )

            city = st.text_input(
                "City"
            )

            contact = st.text_input(
                "Contact"
            )

            email = st.text_input(
                "Email"
            )

            submit = st.form_submit_button(
                "➕ Add Supplier"
            )

            if submit:

                if not name:

                    st.error(
                        "Supplier name is required."
                    )

                else:

                    suppliers.insert_one({
                        "supplier_name": name,
                        "city": city,
                        "contact": contact,
                        "email": email
                    })

                    st.success(
                        "Supplier added to MongoDB!"
                    )

                    st.rerun()

# =========================================================
# STOCK MOVEMENTS
# =========================================================
elif page == "🔄 Stock Movements":

    st.title("🔄 Stock Movement Management")

    st.subheader("Record Stock Movement")

    product_data = list(
        products.find({}, {"_id": 0})
    )

    if product_data:

        product_names = [
            p["product_name"]
            for p in product_data
        ]

        with st.form("movement_form"):

            selected_product = st.selectbox(
                "Product",
                product_names
            )

            movement_type = st.selectbox(
                "Movement Type",
                ["IN", "OUT"]
            )

            quantity = st.number_input(
                "Quantity",
                min_value=1,
                step=1
            )

            movement_date = st.date_input(
                "Movement Date"
            )

            submit = st.form_submit_button(
                "Save Movement"
            )

            if submit:

                product = products.find_one({
                    "product_name":
                    selected_product
                })

                if movement_type == "OUT":

                    if product["quantity"] < quantity:

                        st.error(
                            "Insufficient stock."
                        )

                        st.stop()

                    change = -quantity

                else:

                    change = quantity

                stock_movements.insert_one({
                    "product_name":
                    selected_product,

                    "movement_type":
                    movement_type,

                    "quantity":
                    quantity,

                    "movement_date":
                    str(movement_date),

                    "supplier":
                    product.get(
                        "supplier",
                        ""
                    )
                })

                products.update_one(
                    {
                        "product_name":
                        selected_product
                    },
                    {
                        "$inc":
                        {
                            "quantity":
                            change
                        }
                    }
                )

                st.success(
                    "Stock and MongoDB updated successfully!"
                )

                st.rerun()

    st.markdown("---")

    st.subheader("Movement History")

    data = list(
        stock_movements.find({}, {"_id": 0})
    )

    if data:

        df = pd.DataFrame(data)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

# =========================================================
# ANALYTICS
# =========================================================
elif page == "📊 Analytics":

    st.title("📊 Sales & Inventory Analytics")

    sales_data = list(
        sales.find({}, {"_id": 0})
    )

    product_data = list(
        products.find({}, {"_id": 0})
    )

    if not sales_data:

        st.warning(
            "Not enough sales data for analytics."
        )

    else:

        sales_df = pd.DataFrame(
            sales_data
        )

        product_df = pd.DataFrame(
            product_data
        )

        # -------------------------------------------------
        # Revenue by Product
        # -------------------------------------------------
        st.subheader(
            "💰 Revenue by Product"
        )

        revenue = (
            sales_df
            .groupby("product_name")[
                "total_amount"
            ]
            .sum()
            .reset_index()
        )

        fig1 = px.bar(
            revenue,
            x="product_name",
            y="total_amount",
            title="Revenue by Product",
            labels={
                "product_name": "Product",
                "total_amount": "Revenue"
            }
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

        # -------------------------------------------------
        # Units Sold
        # -------------------------------------------------
        st.subheader(
            "📦 Units Sold by Product"
        )

        units = (
            sales_df
            .groupby("product_name")[
                "quantity"
            ]
            .sum()
            .reset_index()
        )

        fig2 = px.pie(
            units,
            names="product_name",
            values="quantity",
            title="Sales Quantity Distribution"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

        # -------------------------------------------------
        # Category Stock
        # -------------------------------------------------
        if (
            not product_df.empty
            and "category" in product_df.columns
        ):

            st.subheader(
                "📦 Current Stock by Category"
            )

            category_stock = (
                product_df
                .groupby("category")[
                    "quantity"
                ]
                .sum()
                .reset_index()
            )

            fig3 = px.bar(
                category_stock,
                x="category",
                y="quantity",
                title="Inventory by Category",
                labels={
                    "category": "Category",
                    "quantity": "Stock"
                }
            )

            st.plotly_chart(
                fig3,
                use_container_width=True
            )

        # -------------------------------------------------
        # Summary
        # -------------------------------------------------
        st.subheader(
            "📌 Business Summary"
        )

        total_revenue = sales_df[
            "total_amount"
        ].sum()

        total_units = sales_df[
            "quantity"
        ].sum()

        avg_sale = (
            sales_df["total_amount"].mean()
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total Revenue",
            f"₹{total_revenue:,.0f}"
        )

        c2.metric(
            "Units Sold",
            int(total_units)
        )

        c3.metric(
            "Average Sale",
            f"₹{avg_sale:,.0f}"
        )

# =========================================================
# FOOTER
# =========================================================
st.sidebar.markdown("---")
st.sidebar.caption(
    "SmartStock • MongoDB + Python + Streamlit + Pandas"
)