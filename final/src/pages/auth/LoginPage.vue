<template>
  <div
    class="min-h-screen flex flex-col items-center justify-center bg-gray-100 px-4"
  >
    <!-- 標題區 -->
    <div class="text-center mb-12 sm:mb-16">
      <h1 class="text-4xl sm:text-6xl font-extrabold tracking-wide">
        <span class="text-black">開</span>
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-500 animate-pulse"
          >Home</span
        >
        <span class="text-black">爬</span>
      </h1>
      <p class="text-gray-500 text-base sm:text-lg mt-3 sm:mt-4">
        租屋爬蟲通知系統
      </p>
    </div>

    <!-- 登入表單 -->
    <div class="bg-white p-6 sm:p-10 rounded-lg shadow-lg w-full max-w-md">
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
        class="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition text-base sm:text-lg"
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
import { signInWithEmailAndPassword } from "firebase/auth";
import { useAuthStore } from "@/stores/auth";
import { auth } from "@/firebase";

const email = ref("");
const password = ref("");
const errorMsg = ref("");
const router = useRouter();
const authStore = useAuthStore();

const handleLogin = async () => {
  try {
    const cred = await signInWithEmailAndPassword(
      auth,
      email.value,
      password.value
    );
    authStore.setUser(cred.user);
    router.push("/dashboard");
  } catch (error) {
    errorMsg.value = "登入失敗，請檢查帳號密碼是否正確";
  }
};
</script>
