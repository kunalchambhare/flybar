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

    'GOFLOW_URL': "https://fb.goflow.com/",
    'GOFLOW_USERNAME': "Robinb",
    'GOFLOW_PASSWORD': "Robin1600!",

    'local_config': {
        'ODOO_USERNAME': "admin",
        'ODOO_PASSWORD': "admin",
        'ODOO_URL': "localhost",
        'ODOO_PORT': 8069,
        'ODOO_DATABASE': "odoo16_flybar_2",
        'use_odoo_rpc': True
    },

    'staging_config': {
        'ODOO_USERNAME': "admin",
        'ODOO_PASSWORD': "Since@2023",
        'ODOO_URL': "robin-bahadur-flybar-staging-11547131.dev.odoo.com",
        'ODOO_PORT': 80,
        'ODOO_DATABASE': "flybar-staging-11547131",
        'use_odoo_rpc': True
    },

    'production_config': {
        'ODOO_USERNAME': "admin",
        'ODOO_PASSWORD': "Since@2023",
        'ODOO_URL': "https://apps.flybar.com",
        'ODOO_PORT': 80,
        'ODOO_DATABASE': "flybar_production",
        'use_odoo_rpc': False
    }

}
