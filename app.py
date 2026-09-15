import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Cấu hình giao diện Web
st.set_page_config(page_title="Hệ Thống Phân Tích Chi Phí Kho Pro", layout="wide", page_icon="📦")
st.title("📦 HỆ THỐNG PHÂN TÍCH CHI PHÍ KHO & ĐIỀU PHỐI VẬN TẢI")
st.markdown("---")

# Hàm hỗ trợ tìm đúng tên cột
def find_column_name(df, keyword):
    for col in df.columns:
        if keyword.lower() in str(col).lower().replace('\n', ' ').strip():
            return col
    return None

# ==================== THANH BÊN: UPLOAD DỮ LIỆU ====================
st.sidebar.header("📥 1. Upload Dữ liệu Booking")
file_booking = st.sidebar.file_uploader("Tải lên file Booking (Excel/CSV)", type=['csv', 'xlsx'])

if file_booking is not None:
    try:
        # Đọc dữ liệu file Booking
        if file_booking.name.endswith('csv'):
            df_booking = pd.read_csv(file_booking)
        else:
            df_booking = pd.read_excel(file_booking)
            
        # Tự động tìm cột
        col_bien_so = find_column_name(df_booking, 'biển số')
        col_tong_kien = find_column_name(df_booking, 'tổng số kiện')
        col_kho_nhan = find_column_name(df_booking, 'kho nhận')
        col_ngay_giao = find_column_name(df_booking, 'ngày giao')

        if not col_tong_kien or not col_kho_nhan:
            st.error("Lỗi: Không tìm thấy cột 'Tổng số kiện' hoặc 'Kho nhận' trong file Booking.")
            st.stop()
            
        # Xử lý Ngày tháng để chia theo tháng
        if col_ngay_giao:
            df_booking[col_ngay_giao] = pd.to_datetime(df_booking[col_ngay_giao], format='mixed', errors='coerce')
            df_booking['Tháng_Năm'] = df_booking[col_ngay_giao].dt.strftime('Tháng %m/%Y').fillna("Tháng Khác")
            danh_sach_thang = sorted(df_booking['Tháng_Năm'].unique().tolist())
        else:
            df_booking['Tháng_Năm'] = "Tháng Mặc Định"
            danh_sach_thang = ["Tháng Mặc Định"]

        st.sidebar.markdown("---")
        st.sidebar.header("📅 2. Chọn Tháng Phân Tích")
        thang_chon = st.sidebar.selectbox("Chọn tháng báo cáo:", danh_sach_thang)

        # ==================== NHẬP CHI PHÍ THEO TỪNG THÁNG ĐƯỢC CHỌN ====================
        st.sidebar.markdown("---")
        st.sidebar.header(f"💰 3. Nhập Chi Phí Thực Tế ({thang_chon})")
        st.sidebar.info("Nhập chính xác số liệu chi phí thực tế của tháng đang chọn để khớp với Sheet.")

        # Cài đặt giá trị mặc định thông minh theo tháng chọn
        default_ns = 87771141 if "08" in thang_chon else 53746334
        default_vh = 0 if "08" in thang_chon else 9602200
        default_kb = 280221120 if "08" in thang_chon else 27030400
        default_vt = 139749355 if "08" in thang_chon else 232986240

        cp_nhan_su = st.sidebar.number_input("Chi phí Nhân sự (Sau VAT):", value=default_ns, step=1000000)
        cp_van_hanh = st.sidebar.number_input("Chi phí Vận hành (Sau VAT):", value=default_vh, step=1000000)
        cp_kho_bai = st.sidebar.number_input("Chi phí Kho bãi (Sau VAT):", value=default_kb, step=1000000)
        cp_van_tai = st.sidebar.number_input("Tổng Chi phí Vận tải (Sau VAT):", value=default_vt, step=1000000)

        st.sidebar.markdown("---")
        st.sidebar.subheader("Phí Bốc Xếp Phát Sinh Riêng")
        boc_xep_k1 = st.sidebar.number_input("Phí bốc xếp K1:", value=4600000, step=500000)
        boc_xep_k6 = st.sidebar.number_input("Phí bốc xếp K6:", value=7000000, step=500000)
        boc_xep_k16 = st.sidebar.number_input("Phí bốc xếp K16:", value=1800000, step=100000)
        boc_xep_k17 = st.sidebar.number_input("Phí bốc xếp K17:", value=1400000, step=500000)

        st.sidebar.markdown("---")
        st.sidebar.header("🔄 4. Đối Chiếu Tháng Trước")
        thang_truoc_kien = st.sidebar.number_input("Tổng kiện tháng trước:", value=15053, step=1000)
        thang_truoc_tong_chi_phi = st.sidebar.number_input("Tổng chi phí tháng trước (VNĐ):", value=518543159, step=1000000)

        # Lọc dữ liệu theo tháng được chọn
        df_current = df_booking[df_booking['Tháng_Năm'] == thang_chon].copy()
        
        # Làm sạch dữ liệu trong tháng
        df_current[col_tong_kien] = pd.to_numeric(df_current[col_tong_kien], errors='coerce').fillna(0)
        df_current[col_kho_nhan] = df_current[col_kho_nhan].astype(str).str.strip()

        # Tính toán tổng quan tháng được chọn
        tong_so_chuyen = df_current[col_bien_so].nunique() if col_bien_so else 0
        tong_so_kien = df_current[col_tong_kien].sum()
        
        # Tổng chi phí khớp hoàn toàn công thức tổng sheet
        tong_chi_phi = cp_nhan_su + cp_van_hanh + cp_kho_bai + cp_van_tai + boc_xep_k1 + boc_xep_k6 + boc_xep_k16 + boc_xep_k17
        cp_thung_nay = tong_chi_phi / tong_so_kien if tong_so_kien > 0 else 0
        
        # So sánh tháng trước
        delta_chi_phi = tong_chi_phi - thang_truoc_tong_chi_phi
        delta_kien = tong_so_kien - thang_truoc_kien
        pct_chi_phi = (delta_chi_phi / thang_truoc_tong_chi_phi * 100) if thang_truoc_tong_chi_phi else 0

        # Groupby theo Kho trong tháng hiện tại
        df_kho = df_current.groupby(col_kho_nhan)[col_tong_kien].sum().reset_index()
        df_kho = df_kho[df_kho[col_tong_kien] > 0]
        df_kho = df_kho.rename(columns={col_kho_nhan: 'Kho Nhận Hàng', col_tong_kien: 'Tổng Kiện'})
        
        df_kho['Tỷ trọng (%)'] = (df_kho['Tổng Kiện'] / tong_so_kien) * 100
        df_kho['Cước vận tải phân bổ (VNĐ)'] = (df_kho['Tỷ trọng (%)'] / 100) * cp_van_tai
        
        def get_phu_phi(row):
            kho = str(row['Kho Nhận Hàng']).upper()
            if 'K1' in kho and 'K16' not in kho and 'K17' not in kho:
                return boc_xep_k1
            elif 'K6' in kho:
                return boc_xep_k6
            elif 'K16' in kho:
                return boc_xep_k16
            elif 'K17' in kho:
                return boc_xep_k17
            return 0

        df_kho['Phí bốc xếp phát sinh'] = df_kho.apply(get_phu_phi, axis=1)
        df_kho['Chi phí từng thùng (VNĐ)'] = (df_kho['Cước vận tải phân bổ (VNĐ)'] + df_kho['Phí bốc xếp phát sinh']) / df_kho['Tổng Kiện']
        df_kho = df_kho.sort_values('Chi phí từng thùng (VNĐ)', ascending=False)

        # ==================== HIỂN THỊ GIAO DIỆN ====================
        st.subheader(f"📊 1. Tổng Quan Chi Phí & Vận Tải — {thang_chon}")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng Số Chuyến Xe", f"{tong_so_chuyen:,.0f} chuyến")
        col2.metric("Tổng Số Thùng Giao", f"{tong_so_kien:,.0f} thùng", f"{delta_kien:,.0f} thùng")
        col3.metric("Tổng Chi Phí Thực Tế", f"{tong_chi_phi:,.0f} ₫", f"{delta_chi_phi:,.0f} ₫ ({pct_chi_phi:.1f}%)", delta_color="inverse")
        col4.metric("Bình Quân / Thùng", f"{cp_thung_nay:,.0f} ₫")

        # ==================== PHÂN TÍCH NGUYÊN NHÂN TĂNG GIẢM CHI TIẾT ====================
        st.markdown("---")
        st.subheader("🤖 2. Phân Tích Nguyên Nhân & Chỉ Điểm Kho Biến Động")
        
        kho_cao_nhat = df_kho.iloc[0]['Kho Nhận Hàng'] if not df_kho.empty else "N/A"
        chi_phi_kho_cao = df_kho.iloc[0]['Chi phí từng thùng (VNĐ)'] if not df_kho.empty else 0
        
        col_insight1, col_insight2 = st.columns(2)
        with col_insight1:
            st.markdown("##### 🔍 Điểm nóng chi phí (Hotspots):")
            st.info(f"• **Kho có chi phí/thùng cao nhất trong {thang_chon}:** `{kho_cao_nhat}` với mức **{chi_phi_kho_cao:,.0f} ₫/thùng**.\n"
                    f"• **Vấn đề cốt lõi:** Các kho nhỏ hoặc kho phát sinh nhiều phụ phí bốc xếp riêng (K1, K6, K16, K17) đang làm đội giá vốn dịch vụ đơn hàng lên cao.")
        with col_insight2:
            st.markdown("##### 💡 Định hướng cải tiến:")
            if delta_chi_phi > 0:
                st.warning(f"• Tổng chi phí của {thang_chon} cao hơn tháng trước **{delta_chi_phi:,.0f} ₫**.\n"
                           f"• **Hành động:** Kiểm tra kỹ các mục biến phí vận tải và chi phí kho bãi xem có điều chỉnh hợp đồng thuê hoặc tăng giá cước tuyến đường xa hay không.")
            else:
                st.success("• Tổng chi phí đã được tối ưu giảm so với tháng trước. Hiệu suất khai thác kho đang rất tốt.")

        st.markdown("---")
        st.subheader(f"🏭 3. Chi Tiết Chi Phí Từng Thùng Theo Kho Nhận ({thang_chon})")
        c1, c2 = st.columns([1, 1])
        with c1:
            fig = px.bar(df_kho, x='Kho Nhận Hàng', y='Chi phí từng thùng (VNĐ)',
                         title=f"Biểu đồ Chi Phí Từng Thùng / Kho ({thang_chon})", text_auto='.0f', color='Kho Nhận Hàng')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.markdown("**Bảng phân bổ chi tiết theo Kho nhận**")
            st.dataframe(df_kho.style.format({
                    'Tổng Kiện': '{:,.0f}', 
                    'Tỷ trọng (%)': '{:.2f}%', 
                    'Cước vận tải phân bổ (VNĐ)': '{:,.0f} ₫',
                    'Phí bốc xếp phát sinh': '{:,.0f} ₫',
                    'Chi phí từng thùng (VNĐ)': '{:,.0f} ₫'
                }), use_container_width=True)

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi xử lý dữ liệu: {e}")
else:
    st.info("👈 Vui lòng tải file Booking của bạn lên từ thanh công cụ bên trái để bắt đầu tính toán.")
