<script lang="ts">
	import { onMount } from 'svelte';
	import { Card, Spinner, Alert, Tabs, TabItem, Button } from 'flowbite-svelte';
	import { UserCircleOutline, FileDocOutline, DollarOutline, WalletOutline, ClockOutline, ExclamationCircleOutline, ChevronRightOutline, CalendarMonthOutline } from 'flowbite-svelte-icons';
	import { backend } from '$lib/canisters';
	import { principal } from '$lib/stores/auth';
	import { _ } from 'svelte-i18n';
	import ServicesList from './ServicesList.svelte';
	import TaxInformation from './TaxInformation.svelte';
	import PersonalData from './PersonalData.svelte';
	import PaymentAccounts from './PaymentAccounts.svelte';
	
	// Component state
	let loading = true;
	let error = '';
	let summaryData = null;
	let activeTab = 0;
	
	// Get greeting based on time of day
	function getGreeting(): string {
		const hour = new Date().getHours();
		if (hour < 12) return 'Good morning';
		if (hour < 18) return 'Good afternoon';
		return 'Good evening';
	}
	
	// Format the current date nicely
	function formatCurrentDate(): string {
		return new Date().toLocaleDateString('en-US', { 
			weekday: 'long', 
			year: 'numeric', 
			month: 'long', 
			day: 'numeric' 
		});
	}
	
	// Get dashboard summary data for the user
	async function getDashboardSummary() {
		try {
			// Prepare call parameters
			const callParams = { 
				user_id: $principal || 'demo-user'
			};
			
			// Log the request details
			console.log('Calling get_dashboard_summary with parameters:', callParams);
			
			// Use the extension_async_call API method
			const response = await backend.extension_sync_call({
				extension_name: "member_dashboard",
				function_name: "get_dashboard_summary",
				args: JSON.stringify(callParams)
			});
			
			console.log('Dashboard summary response:', response);
			
			if (response.success) {
				// Parse the JSON response
				const data = JSON.parse(response.response);
				console.log('Parsed dashboard summary:', data);
				
				if (data.success) {
					// Handle successful response
					summaryData = data.data;
					console.log('Dashboard summary set:', summaryData);
				} else {
					// Handle error
					error = `Failed to get dashboard summary: ${data.error || 'Unknown error'}`;
					console.error(error);
				}
			} else {
				error = `Failed to get dashboard summary: ${response.response}`;
				console.error(error);
			}
		} catch (err) {
			console.error('Error fetching dashboard summary:', err);
			error = `Error fetching dashboard summary: ${err.message || err}`;
		} finally {
			loading = false;
		}
	}
	
	// Initialize component
	onMount(async () => {
		await getDashboardSummary();
	});
</script>

<div class="w-full max-w-none px-4 py-6">
	<!-- Hero Header Section -->
	<div class="mb-8">
		<div class="flex flex-col lg:flex-row lg:items-center lg:justify-between">
			<div>
				<h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
					{getGreeting()}, <span class="text-blue-600 dark:text-blue-400">{summaryData?.user_name || 'Member'}</span>
				</h1>
				<p class="text-gray-500 dark:text-gray-400 flex items-center">
					<CalendarMonthOutline class="w-4 h-4 mr-2" />
					{formatCurrentDate()}
				</p>
			</div>
			<div class="mt-4 lg:mt-0 flex items-center space-x-3">
				<Button color="light" size="sm" class="flex items-center">
					<ClockOutline class="w-4 h-4 mr-2" />
					View History
				</Button>
				<Button color="blue" size="sm" class="flex items-center">
					Quick Actions
					<ChevronRightOutline class="w-4 h-4 ml-2" />
				</Button>
			</div>
		</div>
	</div>
	
	{#if loading}
		<div class="flex flex-col justify-center items-center p-16 bg-white dark:bg-gray-800 rounded-2xl shadow-sm">
			<Spinner size="12" />
			<p class="mt-4 text-lg text-gray-500 dark:text-gray-400">{$_('extensions.member_dashboard.loading')}</p>
		</div>
	{:else if error}
		<Alert color="red" class="mb-4 rounded-xl">
			<span class="font-medium">{$_('common.error')}:</span> {error}
		</Alert>
	{:else if summaryData}
		<!-- Summary Cards Grid -->
		<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
			<!-- Public Services Card -->
			<div class="group relative bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/40 dark:to-blue-800/30 
						rounded-2xl p-6 border border-blue-200/50 dark:border-blue-700/50 
						shadow-sm hover:shadow-lg hover:scale-[1.02] transition-all duration-300 cursor-pointer"
				 on:click={() => activeTab = 0} on:keypress={() => activeTab = 0} role="button" tabindex="0">
				<div class="flex items-center justify-between mb-4">
					<div class="p-3 bg-blue-500 rounded-xl shadow-lg shadow-blue-500/30">
						<FileDocOutline class="w-6 h-6 text-white" />
					</div>
					<ChevronRightOutline class="w-5 h-5 text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity" />
				</div>
				<h3 class="text-3xl font-bold text-gray-900 dark:text-white mb-1">{summaryData.services_count || 0}</h3>
				<p class="text-sm font-medium text-gray-600 dark:text-gray-300 mb-3">{$_('extensions.member_dashboard.tabs.public_services')}</p>
				{#if summaryData.services_approaching > 0}
					<div class="flex items-center text-amber-600 dark:text-amber-400 text-sm font-medium bg-amber-100 dark:bg-amber-900/30 px-3 py-1.5 rounded-full w-fit">
						<ClockOutline class="w-4 h-4 mr-1.5" />
						{summaryData.services_approaching} approaching
					</div>
				{:else}
					<div class="flex items-center text-green-600 dark:text-green-400 text-sm font-medium">
						✓ All on track
					</div>
				{/if}
			</div>
			
			<!-- Tax Records Card -->
			<div class="group relative bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-900/40 dark:to-emerald-800/30 
						rounded-2xl p-6 border border-emerald-200/50 dark:border-emerald-700/50 
						shadow-sm hover:shadow-lg hover:scale-[1.02] transition-all duration-300 cursor-pointer"
				 on:click={() => activeTab = 1} on:keypress={() => activeTab = 1} role="button" tabindex="0">
				<div class="flex items-center justify-between mb-4">
					<div class="p-3 bg-emerald-500 rounded-xl shadow-lg shadow-emerald-500/30">
						<DollarOutline class="w-6 h-6 text-white" />
					</div>
					<ChevronRightOutline class="w-5 h-5 text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity" />
				</div>
				<h3 class="text-3xl font-bold text-gray-900 dark:text-white mb-1">{summaryData.tax_records || 0}</h3>
				<p class="text-sm font-medium text-gray-600 dark:text-gray-300 mb-3">{$_('extensions.member_dashboard.tabs.my_taxes')}</p>
				{#if summaryData.tax_overdue > 0}
					<div class="flex items-center text-red-600 dark:text-red-400 text-sm font-medium bg-red-100 dark:bg-red-900/30 px-3 py-1.5 rounded-full w-fit">
						<ExclamationCircleOutline class="w-4 h-4 mr-1.5" />
						{summaryData.tax_overdue} overdue
					</div>
				{:else}
					<div class="flex items-center text-green-600 dark:text-green-400 text-sm font-medium">
						✓ No overdue payments
					</div>
				{/if}
			</div>
			
			<!-- Personal Data Card -->
			<div class="group relative bg-gradient-to-br from-violet-50 to-violet-100 dark:from-violet-900/40 dark:to-violet-800/30 
						rounded-2xl p-6 border border-violet-200/50 dark:border-violet-700/50 
						shadow-sm hover:shadow-lg hover:scale-[1.02] transition-all duration-300 cursor-pointer"
				 on:click={() => activeTab = 2} on:keypress={() => activeTab = 2} role="button" tabindex="0">
				<div class="flex items-center justify-between mb-4">
					<div class="p-3 bg-violet-500 rounded-xl shadow-lg shadow-violet-500/30">
						<UserCircleOutline class="w-6 h-6 text-white" />
					</div>
					<ChevronRightOutline class="w-5 h-5 text-violet-400 opacity-0 group-hover:opacity-100 transition-opacity" />
				</div>
				<h3 class="text-3xl font-bold text-gray-900 dark:text-white mb-1">{summaryData.personal_data_items || 0}</h3>
				<p class="text-sm font-medium text-gray-600 dark:text-gray-300 mb-3">{$_('extensions.member_dashboard.tabs.personal_data')}</p>
				{#if summaryData.personal_data_updated > 0}
					<div class="flex items-center text-blue-600 dark:text-blue-400 text-sm font-medium">
						↑ {summaryData.personal_data_updated} recently updated
					</div>
				{:else}
					<div class="flex items-center text-gray-500 dark:text-gray-400 text-sm">
						No recent changes
					</div>
				{/if}
			</div>
			
			<!-- Payment Accounts Card -->
			<div class="group relative bg-gradient-to-br from-amber-50 to-orange-100 dark:from-amber-900/40 dark:to-orange-800/30 
						rounded-2xl p-6 border border-amber-200/50 dark:border-amber-700/50 
						shadow-sm hover:shadow-lg hover:scale-[1.02] transition-all duration-300 cursor-pointer"
				 on:click={() => activeTab = 3} on:keypress={() => activeTab = 3} role="button" tabindex="0">
				<div class="flex items-center justify-between mb-4">
					<div class="p-3 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl shadow-lg shadow-amber-500/30">
						<WalletOutline class="w-6 h-6 text-white" />
					</div>
					<ChevronRightOutline class="w-5 h-5 text-amber-400 opacity-0 group-hover:opacity-100 transition-opacity" />
				</div>
				<h3 class="text-3xl font-bold text-gray-900 dark:text-white mb-1">—</h3>
				<p class="text-sm font-medium text-gray-600 dark:text-gray-300 mb-3">{$_('extensions.member_dashboard.tabs.payment_accounts')}</p>
				<div class="flex items-center text-amber-600 dark:text-amber-400 text-sm font-medium">
					<span class="underline">Set up accounts →</span>
				</div>
			</div>
		</div>
		
		<!-- Content Tabs Section -->
		<div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
			<Tabs style="underline" contentClass="p-6 bg-white dark:bg-gray-800">
				<TabItem open={activeTab === 0} title={$_('extensions.member_dashboard.tabs.public_services')} class="p-4">
					<ServicesList userId={$principal || 'demo-user'} />
				</TabItem>
				
				<TabItem open={activeTab === 1} title={$_('extensions.member_dashboard.tabs.my_taxes')} class="p-4">
					<TaxInformation userId={$principal || 'demo-user'} />
				</TabItem>
				
				<TabItem open={activeTab === 2} title={$_('extensions.member_dashboard.tabs.personal_data')} class="p-4">
					<PersonalData userId={$principal || 'demo-user'} />
				</TabItem>
				
				<TabItem open={activeTab === 3} title={$_('extensions.member_dashboard.tabs.payment_accounts')} class="p-4">
					<PaymentAccounts />
				</TabItem>
			</Tabs>
		</div>
	{:else}
		<Alert color="blue" class="mb-4 rounded-xl">
			{$_('extensions.member_dashboard.no_data')}
		</Alert>
	{/if}
</div>
