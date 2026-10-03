# nutriapp/navigation.py
from kivy.uix.screenmanager import ScreenManager

from nutriapp.screens.auth import AuthScreen
from nutriapp.screens.home import HomeScreen
from nutriapp.screens.profile import ProfileScreen
from nutriapp.screens.products import ProductsScreen
from nutriapp.screens.product_form import ProductFormScreen
from nutriapp.screens.product_details import ProductDetailsScreen
from nutriapp.screens.dishes import DishesScreen
from nutriapp.screens.dish_form import DishFormScreen
from nutriapp.screens.dish_details import DishDetailsScreen
from nutriapp.screens.calendar import CalendarScreen
from nutriapp.screens.diets import DietListScreen
from nutriapp.screens.diet_details import DietDetailsScreen
from nutriapp.screens.shopping import ShoppingScreen
from nutriapp.screens.weight import WeightScreen
from nutriapp.screens.users import UsersScreen
from nutriapp.screens.user_points import UserPointsScreen


def create_root_widget() -> ScreenManager:
    sm = ScreenManager()
    sm.add_widget(AuthScreen(name="auth"))
    sm.add_widget(HomeScreen(name="home"))
    sm.add_widget(ProfileScreen(name="profile"))
    sm.add_widget(ProductsScreen(name="products"))
    sm.add_widget(ProductFormScreen(name="product_form"))
    sm.add_widget(ProductDetailsScreen(name="product_details"))
    sm.add_widget(DishesScreen(name="dishes"))
    sm.add_widget(DishFormScreen(name="dish_form"))
    sm.add_widget(DishDetailsScreen(name="dish_details"))
    sm.add_widget(CalendarScreen(name="calendar"))
    sm.add_widget(DietListScreen(name="diets"))
    sm.add_widget(DietDetailsScreen(name="diet_details"))
    sm.add_widget(ShoppingScreen(name="shopping"))
    sm.add_widget(WeightScreen(name="weight"))
    sm.add_widget(UsersScreen(name="users"))
    sm.add_widget(UserPointsScreen(name="user_points"))
    sm.current = "auth"
    return sm