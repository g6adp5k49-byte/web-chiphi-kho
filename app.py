import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Cấu hình giao diện Web
st.set_page_config(page_title="Hệ Thống Tính Chi Phí Kho", layout="wide", page_icon="📦")
st.title("📦 HỆ THỐNG TỰ ĐỘNG TÍNH TOÁN CHI PHÍ KHO")
st.markdown("---")

# 2. Thanh bên (Sidebar) - Nơi tải dữ liệu đầu vào
st.sidebar.header("📥 Dữ liệu đầu vào")
file_booking = st.sidebar.file_uploader("Tải lên file Booking (Excel/CSV)", type=['csv', 'xlsx'])

st.sidebar.markdown("---")
tong_cuoc_van_tai = st.sidebar.number_input("Tổng phí vận tải tháng (VNĐ):", value=152131755, step=1000000)

if file_booking is not None:
    try:
        # 3. Đọc dữ liệu
        if file_booking.name.endswith('csv'):
            df_booking = pd.read_csv(file_booking)
        else:
            df_booking = pd.read_excel(file_booking)

        # Làm sạch dữ liệu
        df_booking['Tổng số kiện giao'] = pd.to_numeric(df_booking['Tổng số kiện giao'], errors='coerce').fillna(0)

        # 4. ENGINE TÍNH TOÁN
        tong_so_chuyen = df_booking['Biển số xe'].nunique()
        tong_so_kien = df_booking['Tổng số kiện giao'].sum()
        
        # Groupby tính tỷ trọng theo từng kho
        df_kho = df_booking.groupby('Kho nhận hàng')['Tổng số kiện giao'].sum().reset_index()
        df_kho = df_kho[df_kho['Tổng số kiện giao'] > 0]
        
        # Phân bổ chi phí
        df_kho['Tỷ trọng (%)'] = (df_kho['Tổng số kiện giao'] / tong_so_kien) * 100
        df_kho['Phân bổ cước (VNĐ)'] = (df_kho['Tỷ trọng (%)'] / 100) * tong_cuoc_van_tai
        df_kho['Chi phí / Thùng (VNĐ)'] = df_kho['Phân bổ cước (VNĐ)'] / df_kho['Tổng số kiện giao']
        
        df_kho = df_kho.sort_values('Chi phí / Thùng (VNĐ)', ascending=False)

        # 5. HIỂN THỊ
        st.subheader("📊 1. Chỉ số Tổng Quan")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng Số Chuyến Xe", f"{tong_so_chuyen:,.0f}")
        col2.metric("Tổng Số Thùng Giao", f"{tong_so_kien:,.0f}")
        col3.metric("Tổng Phí Vận Tải", f"{tong_cuoc_van_tai:,.0f} ₫")
        col4.metric("Bình quân / Thùng", f"{(tong_cuoc_van_tai/tong_so_kien if tong_so_kien else 0):,.0f} ₫")

        st.markdown("---")
        st.subheader("🏭 2. Phân Bổ Chi Phí Từng Kho")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            fig = px.bar(df_kho, x='Kho nhận hàng', y='Chi phí / Thùng (VNĐ)',
                         title="Chi Phí Từng Thùng Theo Kho Nhận", text_auto='.0f', color='Kho nhận hàng')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.markdown("**Bảng ma trận phân bổ**")
            st.dataframe(
                df_kho.style.format({
                    'Tổng số kiện giao': '{:,.0f}',
                    'Tỷ trọng (%)': '{:.2f}%',
                    'Phân bổ cước (VNĐ)': '{:,.0f} ₫',
                    'Chi phí / Thùng (VNĐ)': '{:,.0f} ₫'
                }), use_container_width=True
            )

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi xử lý dữ liệu: {e}")
else:
    st.info("👈 Vui lòng tải file Booking của bạn lên từ thanh công cụ bên trái để hệ thống bắt đầu tính toán.")
