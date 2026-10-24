import streamlit as st
import pandas as pd
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SmartBus • Enterprise Ticket Booking",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (Dark Theme & Styling) ---
st.markdown("""
<style>
    .metric-card {
        background-color: #12141C;
        border: 1px solid #282D3D;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .ticket-box {
        background-color: #0D0F17;
        border: 2px solid #FACC15;
        border-radius: 16px;
        padding: 24px;
        font-family: monospace;
    }
    .badge-avail {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10B981;
        padding: 3px 8px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: bold;
    }
    .badge-full {
        background-color: rgba(244, 63, 94, 0.15);
        color: #F43F5E;
        padding: 3px 8px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- STATE INITIALIZATION ---
SUPPORTED_CITIES = ("Karachi", "Hyderabad", "Sukkur", "Mirpur Khas", "Lahore")

if "routes" not in st.session_state:
    st.session_state.routes = [
        {"route_id": "R101", "departure_city": "Karachi", "destination_city": "Hyderabad", "departure_time": "08:00 AM", "ticket_price": 1200, "total_seats": 40, "available_seats": 40},
        {"route_id": "R102", "departure_city": "Karachi", "destination_city": "Sukkur", "departure_time": "09:30 AM", "ticket_price": 2000, "total_seats": 36, "available_seats": 36},
        {"route_id": "R103", "departure_city": "Hyderabad", "destination_city": "Mirpur Khas", "departure_time": "11:00 AM", "ticket_price": 800, "total_seats": 32, "available_seats": 32},
        {"route_id": "R104", "departure_city": "Karachi", "destination_city": "Lahore", "departure_time": "07:00 PM", "ticket_price": 5000, "total_seats": 45, "available_seats": 45},
        {"route_id": "R105", "departure_city": "Sukkur", "destination_city": "Hyderabad", "departure_time": "02:00 PM", "ticket_price": 1500, "total_seats": 30, "available_seats": 30}
    ]

if "bookings" not in st.session_state:
    st.session_state.bookings = []

if "booking_counter" not in st.session_state:
    st.session_state.booking_counter = 1001

if "issued_booking_ids" not in st.session_state:
    st.session_state.issued_booking_ids = set()

if "last_booking" not in st.session_state:
    st.session_state.last_booking = None


# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🚌 SmartBus Express")
st.sidebar.caption("Automated Ticketing & Journey Management")

menu = st.sidebar.radio(
    "Go to",
    ["🛣️ Bus Routes", "🎟️ Book Seat", "📋 My Bookings", "📅 City Schedules", "📊 Analytics Dashboard"]
)

# =========================================================
# TAB 1: ROUTES & SEARCH
# =========================================================
if menu == "🛣️ Bus Routes":
    st.title("Available Bus Routes")
    st.caption("Live scheduled trips across Pakistan with real-time seat availability.")

    col_search, col_filter = st.columns([2, 1])
    with col_search:
        search_query = st.text_input("🔍 Search by Route ID or City", "").strip().lower()
    with col_filter:
        filter_opt = st.selectbox("Status Filter", ["All Routes", "Seats Available", "Fully Booked"])

    # Filter Routes
    filtered_routes = []
    for r in st.session_state.routes:
        matches = (
            not search_query
            or search_query in r["route_id"].lower()
            or search_query in r["departure_city"].lower()
            or search_query in r["destination_city"].lower()
        )
        if not matches:
            continue
        if filter_opt == "Seats Available" and r["available_seats"] == 0:
            continue
        if filter_opt == "Fully Booked" and r["available_seats"] > 0:
            continue
        filtered_routes.append(r)

    if not filtered_routes:
        st.warning("No matching bus routes found.")
    else:
        # Display Grid
        cols = st.columns(3)
        for idx, r in enumerate(filtered_routes):
            with cols[idx % 3]:
                is_full = r["available_seats"] == 0
                badge = "🔴 FULLY BOOKED" if is_full else f"🟢 {r['available_seats']} Seats Available"
                
                with st.container(border=True):
                    st.markdown(f"**Route ID:** `{r['route_id']}` &nbsp;|&nbsp; {badge}")
                    st.subheader(f"{r['departure_city']} ➔ {r['destination_city']}")
                    st.write(f"⏰ **Departure:** {r['departure_time']}")
                    st.write(f"💵 **Price:** Rs. {r['ticket_price']:,} / seat")
                    
                    occupancy = (r['total_seats'] - r['available_seats']) / r['total_seats']
                    st.progress(occupancy, text=f"Capacity: {r['available_seats']}/{r['total_seats']} free")

# =========================================================
# TAB 2: SEAT BOOKING WORKFLOW (BR-01 to BR-08)
# =========================================================
elif menu == "🎟️ Book Seat":
    st.title("Reserve Your Seat")
    st.caption("Strict validation rules applied (BR-01 to BR-08)")

    # Route options list
    route_options = {
        f"{r['route_id']} • {r['departure_city']} ➔ {r['destination_city']} ({r['departure_time']}) - Rs. {r['ticket_price']}": r["route_id"]
        for r in st.session_state.routes
    }

    selected_label = st.selectbox("Select Journey Route", list(route_options.keys()))
    selected_route_id = route_options[selected_label]
    route_obj = next(r for r in st.session_state.routes if r["route_id"] == selected_route_id)

    # Route info callout
    col1, col2, col3 = st.columns(3)
    col1.metric("Available Seats", f"{route_obj['available_seats']} / {route_obj['total_seats']}")
    col2.metric("Departure Time", route_obj['departure_time'])
    col3.metric("Ticket Price", f"Rs. {route_obj['ticket_price']:,}")

    with st.form("booking_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            passenger_name = st.text_input("Passenger Full Name *", placeholder="e.g. Ahmed Raza")
            passenger_age = st.number_input("Passenger Age (Years) *", min_value=1, max_value=120, value=25, step=1)
        with c2:
            seats_requested = st.number_input("Seats Requested *", min_value=1, max_value=max(1, route_obj["total_seats"]), value=1, step=1)
            calculated_fare = seats_requested * route_obj["ticket_price"]
            st.metric("Total Fare Payable", f"Rs. {calculated_fare:,}")

        submit = st.form_submit_button("Confirm & Reserve Seat", type="primary", use_container_width=True)

        if submit:
            # BR-01: Name check
            name_clean = passenger_name.strip()
            if not name_clean:
                st.error("Validation Error (BR-01): Passenger name cannot be blank or whitespace-only.")
            # BR-02: Age check
            elif not (1 <= passenger_age <= 120):
                st.error("Validation Error (BR-02): Age must be between 1 and 120.")
            # BR-05: Capacity check
            elif seats_requested > route_obj["available_seats"]:
                st.error(f"Validation Error (BR-05): Cannot reserve {seats_requested} seats. Only {route_obj['available_seats']} seats remaining.")
            else:
                # BR-06: Unique Collision-safe ID
                candidate_id = f"B{st.session_state.booking_counter}"
                while candidate_id in st.session_state.issued_booking_ids:
                    st.session_state.booking_counter += 1
                    candidate_id = f"B{st.session_state.booking_counter}"

                st.session_state.issued_booking_ids.add(candidate_id)
                st.session_state.booking_counter += 1

                # BR-08: Decrement Seats
                route_obj["available_seats"] -= seats_requested

                # Add Record
                booking_record = {
                    "booking_id": candidate_id,
                    "passenger_name": name_clean,
                    "passenger_age": passenger_age,
                    "route_id": route_obj["route_id"],
                    "journey": f"{route_obj['departure_city']} ➔ {route_obj['destination_city']}",
                    "departure_time": route_obj["departure_time"],
                    "seats": seats_requested,
                    "total_fare": calculated_fare,
                    "status": "Confirmed",
                    "timestamp": datetime.now().strftime("%I:%M %p")
                }
                st.session_state.bookings.insert(0, booking_record)
                st.session_state.last_booking = booking_record
                st.success(f"Booking {candidate_id} confirmed for {name_clean}!")
                st.rerun()

    # Boarding Pass Preview if recently booked
    if st.session_state.last_booking:
        b = st.session_state.last_booking
        st.divider()
        st.subheader("Digital Boarding Pass")
        with st.container(border=True):
            b1, b2 = st.columns([3, 1])
            with b1:
                st.markdown(f"### SMART BUS EXPRESS — `#{b['booking_id']}`")
                st.write(f"**Passenger:** {b['passenger_name']} ({b['passenger_age']} yrs)")
                st.write(f"**Route:** {b['journey']} (Route ID: {b['route_id']})")
                st.write(f"**Departure Time:** {b['departure_time']}")
            with b2:
                st.write(f"**Status:** `{b['status']}`")
                st.write(f"**Seats:** {b['seats']}")
                st.markdown(f"### Rs. {b['total_fare']:,}")
                st.caption(f"Issued at {b['timestamp']}")

# =========================================================
# TAB 3: BOOKINGS MANAGEMENT & CANCELLATION (BR-09 to BR-11)
# =========================================================
elif menu == "📋 My Bookings":
    st.title("Booking Management & Ledger")
    st.caption("Cancelled tickets strictly restore capacity only once (BR-09, BR-10, BR-11).")

    if not st.session_state.bookings:
        st.info("No bookings recorded yet. Go to 'Book Seat' to make a reservation.")
    else:
        # Filter Buttons
        filter_status = st.radio("Filter Status", ["All", "Confirmed", "Cancelled"], horizontal=True)
        
        display_list = st.session_state.bookings
        if filter_status != "All":
            display_list = [b for b in display_list if b["status"] == filter_status]

        for b in display_list:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1.5, 2.5, 1.5, 1])
                with c1:
                    st.markdown(f"**ID:** `{b['booking_id']}`")
                    st.write(f"👤 {b['passenger_name']} ({b['passenger_age']}y)")
                with c2:
                    st.write(f"🛣️ **{b['journey']}**")
                    st.caption(f"Route: {b['route_id']} | Dep: {b['departure_time']}")
                with c3:
                    st.write(f"Seats: **{b['seats']}**")
                    if b["status"] == "Confirmed":
                        st.markdown(f"**Rs. {b['total_fare']:,}** &nbsp;🟢 *Confirmed*")
                    else:
                        st.markdown(f"~~Rs. {b['total_fare']:,}~~ &nbsp;🔴 *Cancelled*")
                with c4:
                    if b["status"] == "Confirmed":
                        if st.button("Cancel", key=f"cancel_{b['booking_id']}", type="secondary"):
                            # BR-10: Restore seats
                            route = next((r for r in st.session_state.routes if r["route_id"] == b["route_id"]), None)
                            if route:
                                route["available_seats"] = min(route["total_seats"], route["available_seats"] + b["seats"])
                            
                            # BR-11: Update status to Cancelled
                            b["status"] = "Cancelled"
                            st.toast(f"Booking {b['booking_id']} cancelled. Seats restored to route.")
                            st.rerun()
                    else:
                        st.button("Void", key=f"void_{b['booking_id']}", disabled=True)

# =========================================================
# TAB 4: CITY SCHEDULE MATRIX
# =========================================================
elif menu == "📅 City Schedules":
    st.title("Hub City Departure Schedules")
    st.caption("Departures categorized across regional transport hubs.")

    for city in SUPPORTED_CITIES:
        with st.expander(f"📍 {city.upper()} HUB TERMINAL", expanded=True):
            city_routes = [r for r in st.session_state.routes if r["departure_city"].lower() == city.lower()]
            if not city_routes:
                st.caption(f"No scheduled departures from {city}.")
            else:
                table_data = []
                for r in city_routes:
                    table_data.append({
                        "Route ID": r["route_id"],
                        "Destination": r["destination_city"],
                        "Time": r["departure_time"],
                        "Fare (PKR)": f"Rs. {r['ticket_price']:,}",
                        "Available Capacity": f"{r['available_seats']} / {r['total_seats']} seats"
                    })
                st.table(pd.DataFrame(table_data))

# =========================================================
# TAB 5: ANALYTICS & AUDIT DASHBOARD (BR-12)
# =========================================================
elif menu == "📊 Analytics Dashboard":
    st.title("Executive Intelligence & Revenue Audit")
    st.caption("Cancelled bookings are strictly excluded from confirmed revenue (BR-12).")

    # Metrics
    total_bookings = len(st.session_state.bookings)
    confirmed_bookings = len([b for b in st.session_state.bookings if b["status"] == "Confirmed"])
    cancelled_bookings = len([b for b in st.session_state.bookings if b["status"] == "Cancelled"])
    seats_reserved = sum(b["seats"] for b in st.session_state.bookings if b["status"] == "Confirmed")
    net_revenue = sum(b["total_fare"] for b in st.session_state.bookings if b["status"] == "Confirmed")
    full_routes = len([r for r in st.session_state.routes if r["available_seats"] == 0])

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Bookings", total_bookings)
    m2.metric("Confirmed", confirmed_bookings)
    m3.metric("Cancelled", cancelled_bookings)
    m4.metric("Active Seats", seats_reserved)
    m5.metric("Net Revenue", f"Rs. {net_revenue:,}")
    m6.metric("Full Routes", f"{full_routes} / {len(st.session_state.routes)}")

    st.divider()
    st.subheader("Route-by-Route Financial & Capacity Breakdown")

    route_summary = []
    for r in st.session_state.routes:
        route_confirmed_seats = sum(b["seats"] for b in st.session_state.bookings if b["route_id"] == r["route_id"] and b["status"] == "Confirmed")
        route_revenue = sum(b["total_fare"] for b in st.session_state.bookings if b["route_id"] == r["route_id"] and b["status"] == "Confirmed")
        occupancy_rate = round((route_confirmed_seats / r["total_seats"]) * 100, 1)

        route_summary.append({
            "Route ID": r["route_id"],
            "Journey": f"{r['departure_city']} ➔ {r['destination_city']}",
            "Occupancy": f"{route_confirmed_seats} / {r['total_seats']} ({occupancy_rate}%)",
            "Seats Left": r["available_seats"],
            "Net Revenue": f"Rs. {route_revenue:,}"
        })

    st.dataframe(pd.DataFrame(route_summary), use_container_width=True)

    # Export report download button
    report_text = f"""=========================================================
SMART BUS RESERVATION SYSTEM - EXECUTIVE REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}
=========================================================

Total Bookings Created   : {total_bookings}
Confirmed Active         : {confirmed_bookings}
Cancelled                : {cancelled_bookings}
Active Seats Reserved    : {seats_reserved}
Confirmed Net Revenue    : Rs. {net_revenue:,}
Fully Booked Routes      : {full_routes} of {len(st.session_state.routes)}
"""
    st.download_button(
        label="📥 Download Audit Report (.txt)",
        data=report_text,
        file_name=f"SmartBus_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain"
    )