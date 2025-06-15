import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import { onAuthStateChanged } from "firebase/auth";
import { auth } from "@/firebase";
import { useAuthStore } from "@/stores/auth";
import "./assets/tailwind.css"; // 若你已有

const pinia = createPinia();
const app = createApp(App).use(pinia).use(router);

// ❶ 等 Firebase 判斷完目前 session 再 mount app
onAuthStateChanged(auth, (fbUser) => {
  const authStore = useAuthStore();
  authStore.setUser(fbUser); // ❷ 將使用者同步到 Pinia
  if (!app._container) app.mount("#app");
});
