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
          >Home</span
        >
        <span class="text-black">爬</span>
      </h1>
      <p class="text-gray-500 text-lg mt-4">租屋爬蟲通知系統</p>
    </div>

    <!-- 登入表單 -->
    <div class="bg-white p-10 rounded-lg shadow-lg max-w-lg w-full">
      <div class="mb-6">
        <label class="block mb-2 text-gray-700 font-medium">E-mail</label>
        <input
          v-model="email"
          type="email"
          placeholder="請輸入電子郵件"
          class="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
      </div>

      <div class="mb-6">
        <label class="block mb-2 text-gray-700 font-medium">Password</label>
        <input
          v-model="password"
          type="password"
          placeholder="請輸入密碼"
          class="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
      </div>

      <button
        @click="handleLogin"
        class="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition"
      >
        登入
      </button>

      <router-link
        to="/register"
        class="block text-center text-sm text-blue-600 mt-6 hover:underline"
      >
        註冊帳號
      </router-link>

      <div v-if="errorMsg" class="text-red-500 text-center mt-4">
        {{ errorMsg }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { getAuth, signInWithEmailAndPassword } from "firebase/auth";
import { useAuthStore } from "@/stores/auth";
import { auth } from "@/firebase";

// 資料綁定
const email = ref("");
const password = ref("");
const errorMsg = ref("");
const router = useRouter();
const authStore = useAuthStore(); // ★ ①

const handleLogin = async () => {
  const cred = await signInWithEmailAndPassword(
    auth,
    email.value,
    password.value
  );
  authStore.setUser(cred.user); // 這行非常重要
  router.push("/dashboard");
};
</script>
