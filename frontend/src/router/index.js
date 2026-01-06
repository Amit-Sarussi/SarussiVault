import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/Login.vue';
import MainScreen from '../components/MainScreen.vue';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    name: 'MainScreen',
    component: MainScreen,
    beforeEnter: (to, from, next) => {
      // Check if user is authenticated
      if (localStorage.getItem('fb_token')) {
        next();
      } else {
        next('/login');
      }
    }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;

