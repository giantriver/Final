<template>
  <div
    class="min-h-screen flex flex-col items-center justify-center bg-gray-100"
  >
    <div class="text-center mb-16">
      <h1 class="text-6xl font-extrabold tracking-wide">
        <span class="text-black">開</span>
        <span
          class="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-purple-500 animate-pulse"
          >Home</span
        >
        <span class="text-black">爬</span>
      </h1>
      <p class="text-gray-500 text-lg mt-4">註冊帳號</p>
    </div>

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

      <div class="mb-6">
        <label class="block mb-2 text-gray-700 font-medium">確認密碼</label>
        <input
          v-model="confirmPassword"
          type="password"
          placeholder="請再次輸入密碼"
          class="w-full border border-gray-300 px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
      </div>

      <button
        @click="handleRegister"
        class="w-full bg-green-500 text-white py-3 rounded-lg font-semibold hover:bg-green-600 transition"
      >
        註冊
      </button>

      <router-link
        to="/login"
        class="block text-center text-sm text-blue-600 mt-6 hover:underline"
      >
        已有帳號？前往登入
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
import { auth } from "@/firebase";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { db } from "@/firebase";
import { doc, setDoc } from "firebase/firestore";

const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const errorMsg = ref("");
const router = useRouter();

const handleRegister = async () => {
  errorMsg.value = "";

  if (password.value !== confirmPassword.value) {
    errorMsg.value = "兩次密碼不一致";
    return;
  }

  try {
    const userCredential = await createUserWithEmailAndPassword(
      auth,
      email.value,
      password.value
    );
    const user = userCredential.user;

    // ✅ 寫入 Firestore：儲存 email 至 users 集合中
    await setDoc(doc(db, "users", user.uid), {
      email: email.value,
    });

    router.push("/login");
  } catch (error) {
    console.error(error);
    errorMsg.value = "註冊失敗，請確認帳號是否已存在";
  }
};
</script>
