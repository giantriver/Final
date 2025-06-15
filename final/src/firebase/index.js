// src/firebase/index.js

import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// 這裡填入你自己 Firebase 專案的 config
const firebaseConfig = {
  apiKey: "AIzaSyBaKCZXjslWgcp-6fDQKEtJardCz5rPJVc",
  authDomain: "vue-final-11c0d.firebaseapp.com",
  projectId: "vue-final-11c0d",
  storageBucket: "vue-final-11c0d.firebasestorage.app",
  messagingSenderId: "594797121994",
  appId: "1:594797121994:web:f650f33fb2a1dcd8b53f33",
};

// 初始化 Firebase App
const app = initializeApp(firebaseConfig);

// 初始化各個服務
const auth = getAuth(app);
const db = getFirestore(app);

export { app, auth, db };
