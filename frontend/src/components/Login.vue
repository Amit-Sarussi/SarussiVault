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
	<div class="w-full h-screen flex justify-center items-center p-4 md:p-0">
		<div class="w-full max-w-md flex flex-col justify-center items-center">
			<div class="flex flex-col md:flex-row items-center gap-3 md:gap-6 mb-4 md:mb-2">
				<IconLogo class="w-16 h-16 md:w-24 md:h-24" :draggable="false" />
				<h1 class="text-2xl md:text-5xl font-medium tracking-tight text-center md:text-left">sarussi's vault</h1>
			</div>
			<form @submit.prevent="handleLogin" class="w-full flex flex-col items-center">
				<p class="mb-4 md:mb-6 text-sm md:text-base text-center">Enter you're credentials:</p>
				<div class="w-full flex flex-col gap-3 md:gap-4 mb-4">
					<input
						v-model="username"
						placeholder="Username"
						autocomplete="username"
						class="w-full px-4 py-3 md:py-2 text-base md:text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent" />
					<input
						v-model="password"
						type="password"
						placeholder="Password"
						autocomplete="current-password"
						class="w-full px-4 py-3 md:py-2 text-base md:text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent" />
				</div>
				<div v-if="errorMessage" class="w-full text-red-500 text-xs md:text-sm mb-4 md:mb-6 text-center px-2">
					{{ errorMessage }}
				</div>
				<button
					type="submit"
					class="w-full md:w-auto px-6 py-3 md:py-2 bg-primary cursor-pointer text-white rounded-md hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 transition-colors text-base md:text-sm font-medium">
					Connect
				</button>
			</form>
		</div>
	</div>
</template>
