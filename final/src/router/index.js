import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

import LoginPage from "@/pages/auth/LoginPage.vue";
import RegisterPage from "@/pages/auth/RegisterPage.vue";
import DashboardPage from "@/pages/dashboard/DashboardPage.vue";
import ConditionManagePage from "@/pages/condition/ConditionManagePage.vue";
import NotificationLogPage from "@/pages/notification/NotificationLogPage.vue";

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/login", component: LoginPage },
  { path: "/register", component: RegisterPage },
  {
    path: "/dashboard",
    component: DashboardPage,
    meta: { requiresAuth: true },
  },
  {
    path: "/condition/manage",
    component: ConditionManagePage,
    meta: { requiresAuth: true },
  },
  {
    path: "/notifications",
    component: NotificationLogPage,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 守衛邏輯
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  if (to.meta.requiresAuth && !authStore.user) {
    next("/login");
  } else {
    next();
  }
});

export default router;
