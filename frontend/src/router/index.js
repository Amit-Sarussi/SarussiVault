import { createRouter, createWebHistory } from 'vue-router';
import MainScreen from '../components/MainScreen.vue';
import GuestScreen from '../components/GuestScreen.vue';
import Login from '../components/Login.vue';
import api from '../services/api';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false },
  },
  {
    // Redirect root to shared storage
    path: '/',
    redirect: '/shared',
  },
  {
    // Shared storage: /shared or /shared/path/to/folder
    path: '/shared/:pathMatch(.*)*',
    name: 'MainScreenShared',
    component: MainScreen,
    meta: { requiresAuth: true, storageType: 'shared' },
  },
  {
    // Private storage: /private or /private/path/to/folder
    path: '/private/:pathMatch(.*)*',
    name: 'MainScreenPrivate',
    component: MainScreen,
    meta: { requiresAuth: true, storageType: 'private' },
  },
  {
    // Guest access without path (just shareId) - must come BEFORE pathMatch route
    path: '/open/:shareId',
    name: 'GuestScreenRoot',
    component: GuestScreen,
    meta: { requiresAuth: false, isGuest: true },
  },
  {
    // Guest access: /open/:shareId/path/to/folder
    path: '/open/:shareId/:pathMatch(.*)*',
    name: 'GuestScreen',
    component: GuestScreen,
    meta: { requiresAuth: false, isGuest: true },
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Navigation guard to check authentication
router.beforeEach((to, from, next) => {
  const isAuthenticated = api.isAuthenticated();
  
  // Guest routes don't require authentication - check path pattern as well as meta
  if (to.meta.isGuest || to.path.startsWith('/open/')) {
    next();
    return;
  }
  
  // If user is authenticated and trying to access login, redirect to shared storage
  if (to.path === '/login' && isAuthenticated) {
    next('/shared');
    return;
  }
  
  // If route requires auth and user is not authenticated, redirect to login
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login');
    return;
  }
  
  // If user is not authenticated and trying to access protected route, redirect to login
  // But exclude guest routes from this check
  if (!isAuthenticated && to.path !== '/login' && !to.path.startsWith('/open/')) {
    next('/login');
    return;
  }
  
  next();
});

export default router;

