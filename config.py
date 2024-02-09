DATABASE = 'flybar.db'
JWT_SECRET_KEY = 'SECRET_KEY'
AUTH_TOKEN = ''

DOWNLOAD_DIRECTORY = "/home/ubuntu/Downloads"
MOVE_PATH = '/home/ubuntu/Downloads/UploadedDocs'

selenium_config = {
    'DOWNLOAD_DIRECTORY': "/home/ubuntu/Downloads",
    'MOVE_PATH': '/home/ubuntu/Downloads/UploadedDocs',

    # 'DOWNLOAD_DIRECTORY': "/home/kunal.chambhare/Downloads/",
    # 'MOVE_PATH': '/home/kunal.chambhare/UploadedDocs',

    # 'GOFLOW_URL': "https://fb.goflow.com/",
    # 'GOFLOW_USERNAME': "Robinb",
    # 'GOFLOW_PASSWORD': "Robin1600!",
    'goflow_cred_1': {
        'GOFLOW_URL': "https://bistasolutions.goflow.com/",
        'GOFLOW_USERNAME': "robin.bahadur@bistasolutions.com",
        'GOFLOW_PASSWORD': "Flyb@r2023",
    },

    'goflow_cred_2': {
        'GOFLOW_URL': "https://bistasolutions.goflow.com/",
        'GOFLOW_USERNAME': "robin.bahadur@bistasolutions.com",
        'GOFLOW_PASSWORD': "Flyb@r2023",
    },

    'local_config': {
        'ODOO_USERNAME': "admin",
        'ODOO_PASSWORD': "admin",
        'ODOO_URL': "localhost",
        'ODOO_WEBHOOK_URL': "http://localhost:8069/update_packaging_status_update",
        'AUTH_KEY': "8c2fe0217cc8ae00e373e46ea730dae52575f244",
        'ODOO_PORT': 8069,
        'ODOO_DATABASE': "odoo16_flybar_2",
        'use_odoo_rpc': True
    },

    'staging_config': {
        'ODOO_USERNAME': "admin",
        'ODOO_PASSWORD': "Since@2023",
        'ODOO_URL': "robin-bahadur-flybar-staging-11547131.dev.odoo.com",
        'ODOO_WEBHOOK_URL': "https://robin-bahadur-flybar-staging-11547131.dev.odoo.com/update_packaging_status_update",
        'AUTH_KEY': "8c2fe0217cc8ae00e373e46ea730dae52575f244",
        'ODOO_PORT': 80,
        'ODOO_DATABASE': "robin-bahadur-flybar-staging-11547131",
        'use_odoo_rpc': True
    },

    'production_config': {
        'ODOO_USERNAME': "admin",
        'ODOO_PASSWORD': "Since@2023",
        'ODOO_URL': "https://apps.flybar.com",
        'ODOO_WEBHOOK_URL': "https://apps.flybar.com/update_packaging_status_update",
        'AUTH_KEY': "8c2fe0217cc8ae00e373e46ea730dae52575f244",
        'ODOO_PORT': 80,
        'ODOO_DATABASE': "flybar_production",
        'use_odoo_rpc': False
    }

}
