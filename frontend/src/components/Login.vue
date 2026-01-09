<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "../services/api";
import IconLogo from "@/assets/logo.svg";

const router = useRouter();
const username = ref("");
const password = ref("");
const errorMessage = ref("");

const handleLogin = async () => {
	errorMessage.value = ""; // Clear previous error

	// Check for empty fields
	const usernameEmpty = !username.value.trim();
	const passwordEmpty = !password.value.trim();

	if (usernameEmpty && passwordEmpty) {
		errorMessage.value = "Username and password are required";
		return;
	}
	if (usernameEmpty) {
		errorMessage.value = "Username is required";
		return;
	}
	if (passwordEmpty) {
		errorMessage.value = "Password is required";
		return;
	}

	// Both fields are filled, attempt login
	try {
		await api.login(username.value, password.value);
		// Redirect to home after successful login
		router.push("/");
	} catch (err) {
		errorMessage.value = err.response?.data?.detail || "Wrong credentials";
	}
};
</script>

<template>
	<div class="w-full h-screen flex justify-center items-center">
		<div class="h-full flex flex-col justify-center items-center">
			<div class="flex items-center gap-6 mb-2">
				<IconLogo class="w-24" :draggable="false" />
				<h1 class="text-5xl font-medium tracking-tight">sarussi's vault</h1>
			</div>
			<form @submit.prevent="handleLogin" class="flex flex-col items-center">
				<p class="mb-6">Enter you're credentials:</p>
				<div class="flex flex-col gap-4 mb-4">
					<input
						v-model="username"
						placeholder="Username"
						class="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent" />
					<input
						v-model="password"
						type="password"
						placeholder="Password"
						class="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent" />
				</div>
				<div v-if="errorMessage" class="text-red-500 text-sm mb-6">
					{{ errorMessage }}
				</div>
				<button
					type="submit"
					class="px-4 py-2 bg-primary cursor-pointer text-white rounded-md hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 transition-colors">
					Connect
				</button>
			</form>
		</div>
	</div>
</template>
