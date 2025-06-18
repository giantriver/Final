<template>
  <div class="min-h-screen bg-gray-100 p-6">
    <h1 class="text-3xl font-bold mb-6">條件管理</h1>

    <!-- 新增條件表單 -->
    <div class="bg-white p-4 rounded shadow mb-8">
      <h2 class="text-xl font-semibold mb-4">新增條件</h2>

      <!-- 地區 (市 + 區) -->
      <div class="mb-4">
        <label class="block mb-1 font-medium">地區</label>
        <div class="grid grid-cols-2 gap-4">
          <select v-model="city" @change="updateDistricts" class="input">
            <option value="" disabled>請選擇城市</option>
            <option value="台北市">台北市</option>
            <option value="新北市">新北市</option>
          </select>

          <select v-model="district" class="input">
            <option value="" disabled>請選擇區域</option>
            <option v-for="d in availableDistricts" :key="d" :value="d">
              {{ d }}
            </option>
          </select>
        </div>
      </div>

      <!-- 租金範圍 -->
      <div class="mb-4">
        <label class="block mb-1 font-medium">租金範圍 (元)</label>
        <div class="grid grid-cols-2 gap-4">
          <input
            v-model.number="minPrice"
            type="number"
            placeholder="最低租金"
            class="input"
          />
          <input
            v-model.number="maxPrice"
            type="number"
            placeholder="最高租金"
            class="input"
          />
        </div>
      </div>

      <!-- 坪數範圍 -->
      <div class="mb-4">
        <label class="block mb-1 font-medium">坪數範圍 (坪)</label>
        <div class="grid grid-cols-2 gap-4">
          <input
            v-model.number="minSize"
            type="number"
            placeholder="最小坪數"
            class="input"
          />
          <input
            v-model.number="maxSize"
            type="number"
            placeholder="最大坪數"
            class="input"
          />
        </div>
      </div>

      <!-- 可否養寵物 -->
      <div class="mb-4 flex items-center">
        <input v-model="allowPets" type="checkbox" id="pets" class="mr-2" />
        <label for="pets" class="font-medium">可養寵物</label>
      </div>

      <button
        @click="addCondition"
        class="mt-2 bg-blue-500 text-white py-2 px-4 rounded"
      >
        新增條件
      </button>

      <div v-if="errorMsg" class="text-red-500 mt-3">{{ errorMsg }}</div>
    </div>

    <!-- 條件清單 -->
    <div class="bg-white p-4 rounded shadow">
      <h2 class="text-xl font-semibold mb-4">目前條件</h2>
      <div v-if="conditions.length === 0">尚未新增條件</div>
      <ul>
        <li
          v-for="cond in conditions"
          :key="cond.id"
          class="mb-2 flex justify-between items-center"
        >
          <div>
            {{ cond.city }} {{ cond.district }} | {{ cond.minPrice }} ~
            {{ cond.maxPrice }} 元 | {{ cond.minSize }} ~ {{ cond.maxSize }} 坪
            | {{ cond.allowPets ? "可養寵物" : "不可養寵物" }}
          </div>
          <button
            @click="deleteCondition(cond.id)"
            class="bg-red-500 text-white px-2 py-1 rounded"
          >
            刪除
          </button>
        </li>
      </ul>

      <!-- 立即啟動爬蟲按鈕 -->
      <div class="mt-6">
        <button
          @click="triggerCrawler"
          class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition"
        >
          立即啟動爬蟲
        </button>
        <p v-if="crawlerStatus" class="text-green-600 mt-2 font-semibold">
          {{ crawlerStatus }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";
import { db, auth } from "@/firebase";
import {
  collection,
  addDoc,
  query,
  where,
  getDocs,
  deleteDoc,
  doc,
  serverTimestamp,
} from "firebase/firestore";

const city = ref("");
const district = ref("");
const availableDistricts = ref([]);

const minPrice = ref(0);
const maxPrice = ref(0);
const minSize = ref(0);
const maxSize = ref(0);
const allowPets = ref(false);
const conditions = ref([]);
const errorMsg = ref("");
const crawlerStatus = ref("");

// 城市與對應區域（來自 crawler_591.py 設定）
const cityDistrictMap = {
  台北市: [
    "中正區",
    "大同區",
    "中山區",
    "松山區",
    "大安區",
    "萬華區",
    "信義區",
    "士林區",
    "北投區",
    "內湖區",
    "南港區",
    "文山區",
  ],
  新北市: [
    "板橋區",
    "新莊區",
    "中和區",
    "三重區",
    "新店區",
    "土城區",
    "永和區",
  ],
};

// 根據城市更新可選區域
const updateDistricts = () => {
  district.value = "";
  availableDistricts.value = cityDistrictMap[city.value] || [];
};

// 讀取條件
const loadConditions = async () => {
  const user = auth.currentUser;
  if (!user) return;
  const q = query(
    collection(db, "conditions"),
    where("userId", "==", user.uid)
  );
  const querySnapshot = await getDocs(q);
  conditions.value = querySnapshot.docs.map((doc) => ({
    id: doc.id,
    ...doc.data(),
  }));
};

// 新增條件
const addCondition = async () => {
  const user = auth.currentUser;
  if (!user) {
    errorMsg.value = "尚未登入，請重新登入";
    return;
  }

  if (!city.value || !district.value) {
    errorMsg.value = "請完整選擇城市與區域";
    return;
  }

  try {
    await addDoc(collection(db, "conditions"), {
      userId: user.uid,
      city: city.value,
      district: district.value,
      minPrice: minPrice.value,
      maxPrice: maxPrice.value,
      minSize: minSize.value,
      maxSize: maxSize.value,
      allowPets: allowPets.value,
      createdAt: serverTimestamp(),
    });
    await loadConditions();
    clearForm();
  } catch (err) {
    console.error(err);
    errorMsg.value = "新增條件失敗，請稍後再試";
  }
};

// 呼叫爬蟲 Web API
const triggerCrawler = async () => {
  try {
    await axios.post("https://worker-production-b824.up.railway.app/run");
    crawlerStatus.value = "✅ 已依照條件進行爬蟲";
  } catch (err) {
    console.error("❌ 呼叫爬蟲失敗", err);
    crawlerStatus.value = "❌ 啟動爬蟲失敗，請稍後再試";
  }

  setTimeout(() => {
    crawlerStatus.value = "";
  }, 5000);
};

// 清空表單
const clearForm = () => {
  city.value = "";
  district.value = "";
  availableDistricts.value = [];
  minPrice.value = 0;
  maxPrice.value = 0;
  minSize.value = 0;
  maxSize.value = 0;
  allowPets.value = false;
  errorMsg.value = "";
};

// 刪除條件
const deleteCondition = async (id) => {
  const user = auth.currentUser;
  if (!user) return;
  await deleteDoc(doc(db, "conditions", id));
  await loadConditions();
};

onMounted(() => {
  loadConditions();
  updateDistricts();
});
</script>

<style scoped>
.input {
  @apply w-full border border-gray-300 px-3 py-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-400;
}
</style>
