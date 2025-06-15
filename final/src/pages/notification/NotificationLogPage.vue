<template>
  <div class="min-h-screen bg-gray-100 p-6">
    <h1 class="text-3xl font-bold mb-6">通知紀錄</h1>

    <div class="bg-white p-4 rounded shadow">
      <h2 class="text-xl font-semibold mb-4">符合條件的新物件</h2>

      <div v-if="notifications.length === 0" class="text-gray-500">
        尚無通知紀錄
      </div>

      <ul>
        <li
          v-for="item in notifications"
          :key="item.id"
          class="mb-4 border-b pb-3"
        >
          <div class="flex justify-between items-start">
            <div>
              <a
                :href="item.link"
                target="_blank"
                class="text-blue-600 font-semibold hover:underline text-lg"
              >
                {{ item.title }}
              </a>
              <div class="text-sm text-gray-500 mt-1">{{ item.updated }}</div>
            </div>
            <div class="text-xs text-gray-400">
              {{ formatDate(item.createdAt) }}
            </div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { db, auth } from "@/firebase";
import { collection, query, where, orderBy, getDocs } from "firebase/firestore";

// 通知資料
const notifications = ref([]);

// 日期格式化
const formatDate = (timestamp) => {
  if (!timestamp) return "";
  const date = timestamp.toDate();
  return date.toLocaleString("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const loadNotifications = async () => {
  // 暫時忽略 userId 過濾條件
  const q = query(
    collection(db, "notifications"),
    orderBy("createdAt", "desc")
  );

  const querySnapshot = await getDocs(q);
  notifications.value = querySnapshot.docs.map((doc) => ({
    id: doc.id,
    ...doc.data(),
  }));
};

onMounted(() => {
  loadNotifications();
});
</script>

<style scoped>
/* 使用 Tailwind，無需額外樣式 */
</style>
