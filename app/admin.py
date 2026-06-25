# app/admin.py
from sqladmin import ModelView
# သင့်ရဲ့ Models တွေကို လှမ်း Import လုပ်ပါ
from app.models.user import User
from app.models.role import Role


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.is_active] # Dashboard List မှာ ပြမယ့် Column များ
    column_searchable_list = [User.email]             # ရှာဖွေလို့ရမယ့် Field
    column_filters = [User.is_active]                 # Filter စစ်လို့ရမယ့် Field
    form_columns = [User.email, User.is_active]       # Edit / Create လုပ်ရင် ပြမယ့် Field
    icon = "fa-solid fa-user"                         # ဘေးက ပြမယ့် အိုင်ကွန် (FontAwesome)

class RoleAdmin(ModelView, model=Role):
    column_list = [Role.id, Role.name]
    icon = "fa-solid fa-shield-halved"

# register_admin ဆိုတဲ့ function တစ်ခုဆောက်ထားပြီး main.py ကနေ လှမ်းခေါ်ခိုင်းပါမယ်
def register_admin(admin_instance):
    admin_instance.add_view(UserAdmin)
    admin_instance.add_view(RoleAdmin)