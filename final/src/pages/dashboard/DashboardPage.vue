<template>
  <div
    class="min-h-screen flex flex-col items-center justify-center bg-gray-100"
  >
    <!-- 標題區 -->
    <div class="text-center mb-16">
      <h1 class="text-6xl font-extrabold tracking-wide">
        <span class="text-black">開</span>
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-500 animate-pulse"
        >
          Home
        </span>
        <span class="text-black">爬</span>
      </h1>
      <p class="text-gray-500 text-lg mt-4">租屋爬蟲通知系統</p>
    </div>

    <!-- 導覽按鈕 -->
    <div class="bg-white p-10 rounded-lg shadow-lg max-w-md w-full">
      <div class="space-y-6">
        <button
          @click="goToConditions"
          class="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition"
        >
          條件管理頁
        </button>

        <button
          @click="goToNotifications"
          class="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition"
        >
          通知紀錄頁
        </button>

        <button
          @click="handleLogout"
          class="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition"
        >
          登出
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";
import { auth } from "@/firebase";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const goToConditions = () => {
  router.push("/condition/manage");
};

const goToNotifications = () => {
  router.push("/notifications");
};

const handleLogout = async () => {
  await auth.signOut();
  authStore.clearUser();
  await router.replace("/login");
  // 不要再 router.push()，守衛會自己幫你跳轉
};
</script>

<style scoped>
/* 暫時不需額外樣式，Tailwind已經統一風格 */
</style>
