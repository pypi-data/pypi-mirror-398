def base_css() -> str:
    return """
    /* =========================
       Theme Variables
    ========================== */

    :root {
        --bg-color: #f9fafb;
        --text-color: #111827;
        --card-bg: #ffffff;
        --primary: #2563eb;
        --primary-hover: #1e40af;
        --danger: #dc2626;
        --secondary: #6b7280;
    }

    body.dark {
        --bg-color: #111827;
        --text-color: #f9fafb;
        --card-bg: #1f2933;
    }

    /* =========================
       Base Styles
    ========================== */

    body {
        font-family: Arial, sans-serif;
        padding: 40px;
        background-color: var(--bg-color);
        color: var(--text-color);
    }

    /* =========================
       Layouts
    ========================== */

    .pyui-column {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }

    .pyui-row {
        display: flex;
        flex-direction: row;
        gap: 16px;
        align-items: center;
    }
    /* =========================
        Navbar
        ========================= */

    .pyui-navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 24px;
        background-color: var(--card-bg);
        border-radius: 12px;
        margin-bottom: 24px;
    }

    .pyui-navbar-brand {
        font-size: 20px;
        font-weight: bold;
    }

    .pyui-navbar-links {
        display: flex;
        gap: 20px;
    }

    .pyui-navbar-link {
        cursor: pointer;
        font-size: 15px;
        color: var(--text-color);
    }

    .pyui-navbar-link:hover {
        text-decoration: underline;
    }

    .pyui-navbar-actions {
        display: flex;
        gap: 12px;
    }
    
    /* =========================
    Responsive Grid
    ========================= */

    .pyui-grid {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        gap: 16px;
    }

    .pyui-grid-item {
        grid-column: span var(--span);
    }

    /* Mobile */
    @media (max-width: 768px) {
        .pyui-grid-item {
            grid-column: span 12 !important;
        }
    }


    /* =========================
       Card
    ========================== */

    .pyui-card {
        background-color: var(--card-bg);
        border-radius: 12px;
        padding: 20px;
        max-width: 320px;
    }

    .pyui-card.elevation-1 {
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    }

    .pyui-card.elevation-2 {
        box-shadow: 0 10px 25px rgba(0,0,0,0.12);
    }

    .pyui-card.elevation-3 {
        box-shadow: 0 20px 40px rgba(0,0,0,0.16);
    }

    /* =========================
       Text
    ========================== */

    .pyui-text {
        color: var(--text-color);
    }

    .pyui-text.sm {
        font-size: 14px;
    }

    .pyui-text.md {
        font-size: 16px;
    }

    .pyui-text.lg {
        font-size: 22px;
        font-weight: bold;
    }

    /* =========================
       Button
    ========================== */

    .pyui-button {
        padding: 10px 16px;
        border-radius: 6px;
        border: none;
        color: white;
        font-size: 14px;
        cursor: pointer;
    }

    .pyui-button.primary {
        background-color: var(--primary);
    }

    .pyui-button.primary:hover {
        background-color: var(--primary-hover);
    }

    .pyui-button.danger {
        background-color: var(--danger);
    }

    .pyui-button.secondary {
        background-color: var(--secondary);
    }

    /* =========================
   Form & Input
    ========================= */

    .pyui-form {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }

    .pyui-input-group {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    .pyui-input-label {
        font-size: 14px;
        color: #374151;
    }

    .pyui-input {
        padding: 10px 12px;
        border-radius: 6px;
        border: 1px solid #d1d5db;
        font-size: 14px;
    }

    .pyui-input:focus {
        outline: none;
        border-color: #2563eb;
    }


        /* =========================
    Modal
    ========================= */

    .pyui-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .pyui-modal {
        background-color: white;
        border-radius: 12px;
        width: 100%;
        max-width: 420px;
        padding: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.2);
    }

    .pyui-modal-header {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 12px;
    }

    .pyui-modal-body {
        margin-bottom: 16px;
    }

    .pyui-modal-actions {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
    }

    /* =========================
   Alert
   ========================= */

    .pyui-alert {
        padding: 12px 16px;
        border-radius: 8px;
        font-size: 14px;
    }

    .pyui-alert.success {
        background-color: #dcfce7;
        color: #166534;
    }

    .pyui-alert.error {
        background-color: #fee2e2;
        color: #991b1b;
    }

    .pyui-alert.warning {
        background-color: #fef3c7;
        color: #92400e;
    }

    .pyui-alert.info {
        background-color: #dbeafe;
        color: #1e40af;
    }

    /* =========================
   Toast
========================= */

    .pyui-toast-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 2000;
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .pyui-toast {
        padding: 12px 16px;
        border-radius: 8px;
        font-size: 14px;
        min-width: 240px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.15);
    }

    .pyui-toast.success {
        background-color: #16a34a;
        color: white;
    }

    .pyui-toast.error {
        background-color: #dc2626;
        color: white;
    }

    .pyui-toast.info {
        background-color: #2563eb;
        color: white;
    }

        /* =========================
    Theme Variables
    ========================= */

    :root {
        --bg-color: #f9fafb;
        --text-color: #111827;
        --card-bg: #ffffff;
        --border-color: #e5e7eb;
    }

    [data-theme="dark"] {
        --bg-color: #0f172a;
        --text-color: #e5e7eb;
        --card-bg: #020617;
        --border-color: #334155;
    }


    body {
    background-color: var(--bg-color);
    color: var(--text-color);
    }

    .pyui-card {
        background-color: var(--card-bg);
    }

    .pyui-input {
        border: 1px solid var(--border-color);
    }

    .pyui-link {
        color: #2563eb;
        text-decoration: none;
        font-weight: 500;
    }

    .pyui-link:hover {
        text-decoration: underline;
    }



    


            


    """
