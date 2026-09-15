import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. Cấu hình giao diện Web
st.set_page_config(page_title="Hệ Thống Tính Chi Phí Kho", layout="wide", page_icon="📦")
st.title("📦 HỆ THỐNG TỰ ĐỘNG TÍNH TOÁN CHI PHÍ KHO")
st.markdown("---")

# 2. Thanh bên (Sidebar) - Nơi tải dữ liệu đầu vào
st.sidebar.header("📥 Dữ liệu đầu vào")
file_booking = st.sidebar.file_uploader("Tải lên file Booking (Excel/CSV)", type=['csv', 'xlsx'])

st.sidebar.markdown("---")
tong_cuoc_van_tai = st.sidebar.number_input("Tổng phí vận tải tháng (VNĐ):", value=152131755, step=1000000)

def find_column_name(df, keyword):
    """Hàm tự động tìm tên cột chứa từ khóa (dù bị xuống dòng hay có tiếng Trung)"""
    for col in df.columns:
        # Bỏ dấu tiếng Việt, bỏ khoảng trắng thừa để so sánh
        col_clean = str(col).lower().replace('\n', ' ').strip()
        if keyword.lower() in col_clean:
            return col
    return None

if file_booking is not None:
    try:
        # 3. Đọc dữ liệu
        if file_booking.name.endswith('csv'):
            df_booking = pd.read_csv(file_booking)
        else:
            df_booking = pd.read_excel(file_booking)
            
        # Tự động tìm đúng tên cột trong file tải lên
        col_bien_so = find_column_name(df_booking, 'biển số')
        col_tong_kien = find_column_name(df_booking, 'tổng số kiện')
        col_kho_nhan = find_column_name(df_booking, 'kho nhận')
        
        # Kiểm tra xem có tìm thấy đủ cột không
        if not col_tong_kien or not col_kho_nhan:
            st.error("Không tìm thấy cột 'Tổng số kiện giao' hoặc 'Kho nhận hàng' trong file của bạn. Vui lòng kiểm tra lại file Excel!")
            st.stop() # Dừng chạy nếu lỗi

        # Làm sạch dữ liệu
        df_booking[col_tong_kien] = pd.to_numeric(df_booking[col_tong_kien], errors='coerce').fillna(0)
        df_booking[col_kho_nhan] = df_booking[col_kho_nhan].astype(str).str.strip() # Cắt khoảng trắng thừa

        # 4. ENGINE TÍNH TOÁN
        tong_so_chuyen = df_booking[col_bien_so].nunique() if col_bien_so else 0
        tong_so_kien = df_booking[col_tong_kien].sum()
        
        # Groupby tính tỷ trọng theo từng kho
        df_kho = df_booking.groupby(col_kho_nhan)[col_tong_kien].sum().reset_index()
        df_kho = df_kho[df_kho[col_tong_kien] > 0]
        
        # Đổi tên cột cho dễ nhìn
        df_kho = df_kho.rename(columns={col_kho_nhan: 'Kho Nhận Hàng', col_tong_kien: 'Tổng Kiện'})
        
        # Phân bổ chi phí
        df_kho['Tỷ trọng (%)'] = (df_kho['Tổng Kiện'] / tong_so_kien) * 100
        df_kho['Phân bổ cước (VNĐ)'] = (df_kho['Tỷ trọng (%)'] / 100) * tong_cuoc_van_tai
        df_kho['Chi phí / Thùng (VNĐ)'] = df_kho['Phân bổ cước (VNĐ)'] / df_kho['Tổng Kiện']
        
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
            fig = px.bar(df_kho, x='Kho Nhận Hàng', y='Chi phí / Thùng (VNĐ)',
                         title="Chi Phí Từng Thùng Theo Kho Nhận", text_auto='.0f', color='Kho Nhận Hàng')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.markdown("**Bảng ma trận phân bổ**")
            st.dataframe(
                df_kho.style.format({
                    'Tổng Kiện': '{:,.0f}',
                    'Tỷ trọng (%)': '{:.2f}%',
                    'Phân bổ cước (VNĐ)': '{:,.0f} ₫',
                    'Chi phí / Thùng (VNĐ)': '{:,.0f} ₫'
                }), use_container_width=True
            )

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi xử lý dữ liệu: {e}")
else:
    st.info("👈 Vui lòng tải file Booking của bạn lên từ thanh công cụ bên trái để hệ thống bắt đầu tính toán.")
