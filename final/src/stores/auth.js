import { defineStore } from "pinia";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null, // Firebase 使用者物件
  }),
  actions: {
    setUser(payload) {
      this.user = payload;
    },
    clearUser() {
      this.user = null;
    },
  },
});
