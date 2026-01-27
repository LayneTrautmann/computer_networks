"""
Streamlit Client for Grocery Ordering and Restocking
Sends HTTP/JSON requests to the Flask Ordering Service
"""

import streamlit as st
import requests
import json

# Configuration - Update this when connecting to the Ordering service
ORDERING_SERVICE_URL = "http://localhost:5000"

# Available items per category
ITEMS = {
    "bread": ["white_bread", "wheat_bread", "bagels", "waffles", "croissants", "baguette"],
    "dairy": ["milk", "cheese", "yogurt", "butter", "cream", "eggs"],
    "meat": ["chicken", "beef", "pork", "turkey", "fish", "lamb"],
    "produce": ["tomatoes", "onions", "apples", "oranges", "bananas", "lettuce", "carrots", "potatoes"],
    "party": ["soda", "paper_plates", "napkins", "cups", "balloons", "streamers"]
}

st.set_page_config(page_title="Grocery Service", page_icon="🛒", layout="wide")

st.title("🛒 Automated Grocery Ordering and Delivery Service")

# Tabs for Grocery Order and Restock Order
tab1, tab2 = st.tabs(["📦 Grocery Order (Customer)", "🚚 Restock Order (Supplier)"])

# ============== GROCERY ORDER TAB ==============
with tab1:
    st.header("Place a Grocery Order")
    st.write("Order items from our grocery store for delivery.")

    customer_id = st.text_input("Customer ID", value="customer_001", key="grocery_customer_id")

    st.subheader("Select Items")

    grocery_order_items = {"bread": [], "dairy": [], "meat": [], "produce": [], "party": []}

    col1, col2 = st.columns(2)

    with col1:
        # Bread
        st.write("**🍞 Bread**")
        for item in ITEMS["bread"]:
            qty = st.number_input(f"{item}", min_value=0, max_value=100, value=0, key=f"grocery_bread_{item}")
            if qty > 0:
                grocery_order_items["bread"].append({"name": item, "quantity": qty})

        # Dairy
        st.write("**🥛 Dairy**")
        for item in ITEMS["dairy"]:
            qty = st.number_input(f"{item}", min_value=0, max_value=100, value=0, key=f"grocery_dairy_{item}")
            if qty > 0:
                grocery_order_items["dairy"].append({"name": item, "quantity": qty})

        # Meat
        st.write("**🥩 Meat**")
        for item in ITEMS["meat"]:
            qty = st.number_input(f"{item}", min_value=0, max_value=100, value=0, key=f"grocery_meat_{item}")
            if qty > 0:
                grocery_order_items["meat"].append({"name": item, "quantity": qty})

    with col2:
        # Produce
        st.write("**🥬 Produce**")
        for item in ITEMS["produce"]:
            qty = st.number_input(f"{item}", min_value=0, max_value=100, value=0, key=f"grocery_produce_{item}")
            if qty > 0:
                grocery_order_items["produce"].append({"name": item, "quantity": qty})

        # Party Supplies
        st.write("**🎉 Party Supplies**")
        for item in ITEMS["party"]:
            qty = st.number_input(f"{item}", min_value=0, max_value=100, value=0, key=f"grocery_party_{item}")
            if qty > 0:
                grocery_order_items["party"].append({"name": item, "quantity": qty})

    if st.button("Submit Grocery Order", type="primary", key="submit_grocery"):
        # Check if at least one item is ordered
        total_items = sum(len(items) for items in grocery_order_items.values())

        if total_items == 0:
            st.error("Please select at least one item to order.")
        else:
            # Build the order payload
            order_payload = {
                "customer_id": customer_id,
                "order_type": "GROCERY_ORDER",
                "items": grocery_order_items
            }

            st.write("**Order Payload (JSON):**")
            st.json(order_payload)

            # Send to Ordering service
            try:
                response = requests.post(
                    f"{ORDERING_SERVICE_URL}/order/grocery",
                    json=order_payload,
                    timeout=10
                )

                if response.status_code == 200:
                    st.success("Order submitted successfully!")
                    st.write("**Response:**")
                    st.json(response.json())
                else:
                    st.error(f"Order failed with status code: {response.status_code}")
                    st.write(response.text)

            except requests.exceptions.ConnectionError:
                st.warning("Could not connect to Ordering Service. Showing order payload only.")
                st.info("Start the Ordering Service at http://localhost:5000 to process orders.")


# ============== RESTOCK ORDER TAB ==============
with tab2:
    st.header("Submit a Restock Order")
    st.write("Restock inventory from supplier truck delivery.")

    supplier_id = st.text_input("Supplier ID", value="supplier_001", key="restock_supplier_id")

    st.subheader("Select Items to Restock")

    restock_order_items = {"bread": [], "dairy": [], "meat": [], "produce": [], "party": []}

    col1, col2 = st.columns(2)

    with col1:
        # Bread
        st.write("**🍞 Bread**")
        for item in ITEMS["bread"]:
            qty = st.number_input(f"{item}", min_value=0, max_value=1000, value=0, key=f"restock_bread_{item}")
            if qty > 0:
                restock_order_items["bread"].append({"name": item, "quantity": qty})

        # Dairy
        st.write("**🥛 Dairy**")
        for item in ITEMS["dairy"]:
            qty = st.number_input(f"{item}", min_value=0, max_value=1000, value=0, key=f"restock_dairy_{item}")
            if qty > 0:
                restock_order_items["dairy"].append({"name": item, "quantity": qty})

        # Meat
        st.write("**🥩 Meat**")
        for item in ITEMS["meat"]:
            qty = st.number_input(f"{item}", min_value=0, max_value=1000, value=0, key=f"restock_meat_{item}")
            if qty > 0:
                restock_order_items["meat"].append({"name": item, "quantity": qty})

    with col2:
        # Produce
        st.write("**🥬 Produce**")
        for item in ITEMS["produce"]:
            qty = st.number_input(f"{item}", min_value=0, max_value=1000, value=0, key=f"restock_produce_{item}")
            if qty > 0:
                restock_order_items["produce"].append({"name": item, "quantity": qty})

        # Party Supplies
        st.write("**🎉 Party Supplies**")
        for item in ITEMS["party"]:
            qty = st.number_input(f"{item}", min_value=0, max_value=1000, value=0, key=f"restock_party_{item}")
            if qty > 0:
                restock_order_items["party"].append({"name": item, "quantity": qty})

    if st.button("Submit Restock Order", type="primary", key="submit_restock"):
        # Check if at least one item is being restocked
        total_items = sum(len(items) for items in restock_order_items.values())

        if total_items == 0:
            st.error("Please select at least one item to restock.")
        else:
            # Build the restock payload
            restock_payload = {
                "supplier_id": supplier_id,
                "order_type": "RESTOCK_ORDER",
                "items": restock_order_items
            }

            st.write("**Restock Payload (JSON):**")
            st.json(restock_payload)

            # Send to Ordering service
            try:
                response = requests.post(
                    f"{ORDERING_SERVICE_URL}/order/restock",
                    json=restock_payload,
                    timeout=10
                )

                if response.status_code == 200:
                    st.success("Restock order submitted successfully!")
                    st.write("**Response:**")
                    st.json(response.json())
                else:
                    st.error(f"Restock order failed with status code: {response.status_code}")
                    st.write(response.text)

            except requests.exceptions.ConnectionError:
                st.warning("Could not connect to Ordering Service. Showing restock payload only.")
                st.info("Start the Ordering Service at http://localhost:5000 to process orders.")


# ============== SIDEBAR INFO ==============
with st.sidebar:
    st.header("About")
    st.write("""
    This is the client interface for the Automated Grocery Ordering and Delivery Service.

    **Client Types:**
    - **Grocery Order**: Simulates a smart refrigerator placing an order
    - **Restock Order**: Simulates a supplier truck restocking inventory

    **Communication:**
    - Protocol: HTTP
    - Format: JSON
    - Endpoint: Flask Ordering Service
    """)

    st.header("Service Status")
    try:
        response = requests.get(f"{ORDERING_SERVICE_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ Ordering Service: Online")
        else:
            st.error("❌ Ordering Service: Error")
    except:
        st.warning("⚠️ Ordering Service: Offline")

    st.header("Configuration")
    st.code(f"Ordering Service URL:\n{ORDERING_SERVICE_URL}")
