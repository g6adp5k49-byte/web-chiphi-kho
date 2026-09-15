import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Cấu hình giao diện Web
st.set_page_config(page_title="Hệ Thống Phân Tích Chi Phí Kho & Vận Tải Pro", layout="wide", page_icon="📊")
st.title("📊 HỆ THỐNG QUẢN TRỊ CHI PHÍ KHO & VẬN TẢI (CHUẨN GOOGLE SHEETS)")
st.markdown("---")

# Danh sách chuẩn 25 kho / bộ phận
STANDARD_WAREHOUSES = [
    'K0', 'K1', 'K2', 'K5', 'K6', 'K7', 'K8', 'K9', 
    'K13', 'K14', 'K15', 'K16', 'K17', 'K18', 'K19', 'K20', 
    'CHIA HÀNG', 'ECOM', 'MKT', 'PKD', 'HỦY HÀNG', 'THU HỒI', 'CÔNG TRÌNH', 'OP', 'HR'
]

def find_column_name(df, keyword):
    for col in df.columns:
        if keyword.lower() in str(col).lower().replace('\n', ' ').strip():
            return col
    return None

# ==================== THANH BÊN: UPLOAD DỮ LIỆU & NHẬP LIỆU ====================
st.sidebar.header("📥 1. Upload Dữ liệu Booking")
file_booking = st.sidebar.file_uploader("Tải lên file Booking (Excel/CSV)", type=['csv', 'xlsx'])

st.sidebar.markdown("---")
st.sidebar.header("💰 2. Nhập Chi Phí Chi Tiết (Trước & Sau VAT)")
st.sidebar.info("Nhập chính xác số liệu Trước VAT và Sau VAT (8%) khớp với Google Sheets Tháng 8.")

st.sidebar.subheader("1. Chi phí Nhân sự (HR)")
ns_truoc = st.sidebar.number_input("Nhân sự - Trước VAT:", value=81269575, step=1000000)
ns_sau = st.sidebar.number_input("Nhân sự - Sau VAT (8%):", value=87771141, step=1000000)

st.sidebar.subheader("2. Chi phí Vận hành")
vh_truoc = st.sidebar.number_input("Vận hành - Trước VAT:", value=0, step=1000000)
vh_sau = st.sidebar.number_input("Vận hành - Sau VAT (8%):", value=0, step=1000000)

st.sidebar.subheader("3. Chi phí Kho bãi")
kb_truoc = st.sidebar.number_input("Kho bãi - Trước VAT:", value=259464000, step=1000000)
kb_sau = st.sidebar.number_input("Kho bãi - Sau VAT (8%):", value=280221120, step=1000000)

st.sidebar.subheader("4. Tổng Chi phí Vận tải")
vt_truoc = st.sidebar.number_input("Vận tải - Trước VAT:", value=129397551, step=1000000)
vt_sau = st.sidebar.number_input("Vận tải - Sau VAT (8%):", value=139749355, step=1000000)

st.sidebar.markdown("---")
st.sidebar.subheader("Phí Bốc Xếp Phát Sinh Riêng (Theo Kho)")
boc_xep_k1 = st.sidebar.number_input("Phí bốc xếp K1:", value=4600000, step=500000)
boc_xep_k6 = st.sidebar.number_input("Phí bốc xếp đợt 2 (K6):", value=7000000, step=500000)
boc_xep_k16 = st.sidebar.number_input("Phí bốc xếp K16:", value=1800000, step=100000)
boc_xep_k17 = st.sidebar.number_input("Phí bốc xếp K17:", value=1400000, step=500000)

st.sidebar.markdown("---")
st.sidebar.header("🔄 3. Đối Chiếu Tháng Trước")
thang_truoc_kien = st.sidebar.number_input("Tổng kiện tháng trước:", value=15053, step=1000)
thang_truoc_tong_chi_phi = st.sidebar.number_input("Tổng chi phí tháng trước (Sau VAT):", value=518543159, step=1000000)

# ==================== XỬ LÝ DỮ LIỆU CHÍNH ====================
if file_booking is not None:
    try:
        if file_booking.name.endswith('csv'):
            df_booking = pd.read_csv(file_booking)
        else:
            df_booking = pd.read_excel(file_booking)
            
        col_bien_so = find_column_name(df_booking, 'biển số')
        col_tong_kien = find_column_name(df_booking, 'tổng số kiện')
        col_kho_nhan = find_column_name(df_booking, 'kho nhận')
        col_ngay_giao = find_column_name(df_booking, 'ngày giao')

        if not col_tong_kien or not col_kho_nhan:
            st.error("Lỗi: Không tìm thấy cột 'Tổng số kiện' hoặc 'Kho nhận' trong file Booking.")
            st.stop()
            
        if col_ngay_giao:
            df_booking[col_ngay_giao] = pd.to_datetime(df_booking[col_ngay_giao], format='mixed', errors='coerce')
            df_booking['Tháng_Năm'] = df_booking[col_ngay_giao].dt.strftime('Tháng %m/%Y').fillna("Tháng Khác")
            danh_sach_thang = sorted(df_booking['Tháng_Năm'].unique().tolist())
        else:
            df_booking['Tháng_Năm'] = "Tháng Mặc Định"
            danh_sach_thang = ["Tháng Mặc Định"]

        st.sidebar.markdown("---")
        st.sidebar.header("📅 4. Chọn Tháng Phân Tích")
        thang_chon = st.sidebar.selectbox("Chọn tháng báo cáo:", danh_sach_thang)

        # Lọc dữ liệu theo tháng
        df_current = df_booking[df_booking['Tháng_Năm'] == thang_chon].copy()
        df_current[col_tong_kien] = pd.to_numeric(df_current[col_tong_kien], errors='coerce').fillna(0)
        df_current[col_kho_nhan] = df_current[col_kho_nhan].astype(str).str.strip().str.upper()

        tong_so_chuyen = df_current[col_bien_so].nunique() if col_bien_so else 0
        tong_so_kien = df_current[col_tong_kien].sum()
        
        # Tổng chi phí Trước VAT và Sau VAT chuẩn theo Sheet
        tong_chi_phi_truoc = ns_truoc + vh_truoc + kb_truoc + vt_truoc
        tong_chi_phi_sau = ns_sau + vh_sau + kb_sau + vt_sau + boc_xep_k1 + boc_xep_k6 + boc_xep_k16 + boc_xep_k17
        
        cp_thung_nay = tong_chi_phi_sau / tong_so_kien if tong_so_kien > 0 else 0
        
        delta_chi_phi = tong_chi_phi_sau - thang_truoc_tong_chi_phi
        delta_kien = tong_so_kien - thang_truoc_kien
        pct_chi_phi = (delta_chi_phi / thang_truoc_tong_chi_phi * 100) if thang_truoc_tong_chi_phi else 0

        # Xây dựng ma trận chi tiết theo đúng 25 kho chuẩn
        agg_data = df_current.groupby(col_kho_nhan)[col_tong_kien].sum().to_dict()
        
        matrix_rows = []
        for wh in STANDARD_WAREHOUSES:
            kien = agg_data.get(wh, 0.0)
            ty_trong = (kien / tong_so_kien * 100) if tong_so_kien > 0 else 0.0
            cuoc_vt = (ty_trong / 100.0) * vt_sau
            
            phu_phi = 0
            if wh == 'K1': phu_phi = boc_xep_k1
            elif wh == 'K6': phu_phi = boc_xep_k6
            elif wh == 'K16': phu_phi = boc_xep_k16
            elif wh == 'K17': phu_phi = boc_xep_k17
            
            chi_phi_tong_wh = cuoc_vt + phu_phi
            don_gia_thung = (chi_phi_tong_wh / kien) if kien > 0 else 0.0
            
            matrix_rows.append({
                'Kho / Bộ phận': wh,
                'Số Kiện': kien,
                'Tỷ trọng (%)': ty_trong,
                'Cước vận tải (VNĐ)': cuoc_vt,
                'Phí bốc xếp phát sinh': phu_phi,
                'Chi phí từng thùng (VNĐ)': don_gia_thung
            })
        
        df_matrix = pd.DataFrame(matrix_rows)

        # ==================== HIỂN THỊ GIAO DIỆN CHÍNH ====================
        st.subheader(f"📈 1. Tổng Quan Chỉ Số Tài Chính — {thang_chon}")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng Số Chuyến Xe", f"{tong_so_chuyen:,.0f} chuyến")
        col2.metric("Tổng Số Thùng Giao", f"{tong_so_kien:,.0f} thùng", f"{delta_kien:,.0f} thùng")
        col3.metric("Tổng Chi Phí (Sau VAT)", f"{tong_chi_phi_sau:,.0f} ₫", f"{delta_chi_phi:,.0f} ₫ ({pct_chi_phi:.1f}%)", delta_color="inverse")
        col4.metric("Bình Quân / Thùng", f"{cp_thung_nay:,.0f} ₫")

        # ==================== BẢNG 1: KÊ CHI TIẾT CÁC KHOAN PHÍ ====================
        st.markdown("---")
        st.subheader("📋 2. Bảng Kê Chi Tiết Các Khoản Phí (Trước VAT & Sau VAT 8%)")
        
        detail_costs = [
            {"Hạng mục Chi Phí": "Chi phí Nhân sự", "Trước VAT (VNĐ)": ns_truoc, "Thanh toán (Gồm 8% VAT)": ns_sau, "Đơn giá/Thùng": ns_sau / tong_so_kien if tong_so_kien > 0 else 0},
            {"Hạng mục Chi Phí": "Chi phí Vận hành", "Trước VAT (VNĐ)": vh_truoc, "Thanh toán (Gồm 8% VAT)": vh_sau, "Đơn giá/Thùng": vh_sau / tong_so_kien if tong_so_kien > 0 else 0},
            {"Hạng mục Chi Phí": "Chi phí Kho bãi", "Trước VAT (VNĐ)": kb_truoc, "Thanh toán (Gồm 8% VAT)": kb_sau, "Đơn giá/Thùng": kb_sau / tong_so_kien if tong_so_kien > 0 else 0},
            {"Hạng mục Chi Phí": "Tổng Chi phí Vận tải", "Trước VAT (VNĐ)": vt_truoc, "Thanh toán (Gồm 8% VAT)": vt_sau, "Đơn giá/Thùng": vt_sau / tong_so_kien if tong_so_kien > 0 else 0},
            {"Hạng mục Chi Phí": "Phí bốc xếp phát sinh K1", "Trước VAT (VNĐ)": boc_xep_k1, "Thanh toán (Gồm 8% VAT)": boc_xep_k1, "Đơn giá/Thùng": boc_xep_k1 / tong_so_kien if tong_so_kien > 0 else 0},
            {"Hạng mục Chi Phí": "Phí bốc xếp phát sinh K6", "Trước VAT (VNĐ)": boc_xep_k6, "Thanh toán (Gồm 8% VAT)": boc_xep_k6, "Đơn giá/Thùng": boc_xep_k6 / tong_so_kien if tong_so_kien > 0 else 0},
            {"Hạng mục Chi Phí": "Phí bốc xếp phát sinh K16", "Trước VAT (VNĐ)": boc_xep_k16, "Thanh toán (Gồm 8% VAT)": boc_xep_k16, "Đơn giá/Thùng": boc_xep_k16 / tong_so_kien if tong_so_kien > 0 else 0},
            {"Hạng mục Chi Phí": "Phí bốc xếp phát sinh K17", "Trước VAT (VNĐ)": boc_xep_k17, "Thanh toán (Gồm 8% VAT)": boc_xep_k17, "Đơn giá/Thùng": boc_xep_k17 / tong_so_kien if tong_so_kien > 0 else 0},
        ]
        df_detail = pd.DataFrame(detail_costs)
        
        # Thêm dòng Tổng cộng
        total_row = pd.DataFrame([{
            "Hạng mục Chi Phí": "TỔNG CỘNG", 
            "Trước VAT (VNĐ)": tong_chi_phi_truoc, 
            "Thanh toán (Gồm 8% VAT)": tong_chi_phi_sau, 
            "Đơn giá/Thùng": cp_thung_nay
        }])
        df_detail = pd.concat([df_detail, total_row], ignore_index=True)

        st.dataframe(df_detail.style.format({
            'Trước VAT (VNĐ)': '{:,.0f} ₫',
            'Thanh toán (Gồm 8% VAT)': '{:,.0f} ₫',
            'Đơn giá/Thùng': '{:,.0f} ₫'
        }), use_container_width=True)

        # ==================== BẢNG 2: MA TRẬN TỔNG HỢP THEO KHO ====================
        st.markdown("---")
        st.subheader("🗂️ 3. Ma Trận Tổng Hợp Sản Lượng & Đơn Giá Từng Thùng Theo Kho")
        
        df_pivot = df_matrix.set_index('Kho / Bộ phận')[['Số Kiện', 'Tỷ trọng (%)', 'Cước vận tải (VNĐ)', 'Chi phí từng thùng (VNĐ)']].T
        st.dataframe(df_pivot.style.format("{:,.2f}"), use_container_width=True)

        # Biểu đồ trực quan
        st.markdown("---")
        st.subheader(f"📊 4. Biểu Đồ Chi Phí Từng Thùng Theo Từng Kho ({thang_chon})")
        fig = px.bar(df_matrix[df_matrix['Số Kiện'] > 0], x='Kho / Bộ phận', y='Chi phí từng thùng (VNĐ)',
                     title=f"Đơn Giá Chi Phí / Thùng Theo Từng Kho ({thang_chon})", text_auto=',.0f', color='Kho / Bộ phận')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi xử lý dữ liệu: {e}")
else:
    st.info("👈 Vui lòng tải file Booking của bạn lên từ thanh công cụ bên trái để hệ thống hiển thị đầy đủ bảng báo cáo.")
