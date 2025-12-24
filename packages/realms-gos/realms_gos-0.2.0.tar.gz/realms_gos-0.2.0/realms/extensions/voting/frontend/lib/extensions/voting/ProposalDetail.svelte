<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { Card, Button, Badge, Alert, Spinner } from 'flowbite-svelte';
	import { LinkOutline, CalendarMonthOutline, UserCircleSolid, CodeBranchOutline, CheckCircleSolid, PlaySolid } from 'flowbite-svelte-icons';
	import { _ } from 'svelte-i18n';
	import { backend } from '$lib/canisters';
	import VotingCard from './VotingCard.svelte';
	
	export let proposal;
	
	const dispatch = createEventDispatcher();
	
	// Code fetching state
	let codeContent = '';
	let codeLoading = true;
	let codeError = '';
	let codeChecksum = '';
	
	// Demo feature state
	let approving = false;
	let executing = false;
	let actionError = '';
	let actionSuccess = '';
	
	onMount(async () => {
		await fetchCode();
	});
	
	async function fetchCode() {
		try {
			codeLoading = true;
			codeError = '';
			
			const response = await backend.extension_async_call({
				extension_name: "voting",
				function_name: "fetch_proposal_code",
				args: JSON.stringify({ proposal_id: proposal.id })
			});
			
			if (response.success) {
				const data = typeof response.response === 'string' 
					? JSON.parse(response.response) 
					: response.response;
				
				if (data.success) {
					codeContent = data.data.code;
					codeChecksum = data.data.checksum;
				} else {
					codeError = data.error || 'Failed to fetch code';
				}
			} else {
				codeError = 'Failed to communicate with backend';
			}
		} catch (e) {
			console.error('Error fetching code:', e);
			codeError = 'Error fetching code: ' + e.message;
		} finally {
			codeLoading = false;
		}
	}
	
	async function handleApprove() {
		try {
			approving = true;
			actionError = '';
			actionSuccess = '';
			
			const response = await backend.extension_sync_call({
				extension_name: "voting",
				function_name: "approve_proposal",
				args: JSON.stringify({ proposal_id: proposal.id })
			});
			
			if (response.success) {
				const data = typeof response.response === 'string' 
					? JSON.parse(response.response) 
					: response.response;
				
				if (data.success) {
					actionSuccess = data.data.message;
					proposal.status = 'accepted';
					dispatch('statusChanged', { proposal_id: proposal.id, status: 'accepted' });
				} else {
					actionError = data.error || 'Failed to approve proposal';
				}
			} else {
				actionError = 'Failed to communicate with backend';
			}
		} catch (e) {
			console.error('Error approving proposal:', e);
			actionError = 'Error: ' + e.message;
		} finally {
			approving = false;
		}
	}
	
	async function handleExecute() {
		try {
			executing = true;
			actionError = '';
			actionSuccess = '';
			
			const response = await backend.extension_async_call({
				extension_name: "voting",
				function_name: "execute_proposal",
				args: JSON.stringify({ proposal_id: proposal.id })
			});
			
			if (response.success) {
				const data = typeof response.response === 'string' 
					? JSON.parse(response.response) 
					: response.response;
				
				if (data.success) {
					actionSuccess = data.data.message;
					proposal.status = 'executed';
					dispatch('statusChanged', { proposal_id: proposal.id, status: 'executed' });
				} else {
					actionError = data.error || 'Failed to execute proposal';
				}
			} else {
				actionError = 'Failed to communicate with backend';
			}
		} catch (e) {
			console.error('Error executing proposal:', e);
			actionError = 'Error: ' + e.message;
		} finally {
			executing = false;
		}
	}
	
	function getStatusColor(status: string) {
		switch (status) {
			case 'pending_review': return 'yellow';
			case 'pending_vote': return 'blue';
			case 'voting': return 'green';
			case 'accepted': return 'purple';
			case 'executed': return 'indigo';
			case 'rejected': return 'red';
			default: return 'gray';
		}
	}
	
	function formatDate(dateString: string) {
		if (!dateString) return 'N/A';
		return new Date(dateString).toLocaleString();
	}
	
	function handleVote(event) {
		dispatch('vote', event.detail);
	}
	
	function handleClose() {
		dispatch('close');
	}
</script>

<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
			<!-- Left Column: Proposal Details -->
			<div class="space-y-6 overflow-y-auto max-h-[70vh]">
				<!-- Proposal Header -->
				<div>
					<div class="flex items-center gap-3 mb-3">
						<h2 class="text-2xl font-bold text-gray-900">
							{proposal.title}
						</h2>
						<Badge color={getStatusColor(proposal.status)} size="lg">
							{$_(`extensions.voting.status.${proposal.status}`)}
						</Badge>
					</div>
					
					<div class="flex items-center gap-4 text-sm text-gray-600">
						<div class="flex items-center gap-1">
							<UserCircleSolid class="w-4 h-4" />
							<span>{$_('extensions.voting.detail.proposer')}: {proposal.proposer}</span>
						</div>
						<div class="flex items-center gap-1">
							<CalendarMonthOutline class="w-4 h-4" />
							<span>{$_('extensions.voting.detail.created')}: {formatDate(proposal.created_at)}</span>
						</div>
					</div>
					
					{#if proposal.voting_deadline}
						<div class="flex items-center gap-1 text-sm text-gray-600 mt-1">
							<CalendarMonthOutline class="w-4 h-4" />
							<span>{$_('extensions.voting.detail.deadline')}: {formatDate(proposal.voting_deadline)}</span>
						</div>
					{/if}
					{#if proposal.code_url}
						<div class="flex items-center gap-1 text-sm">
							<LinkOutline class="w-4 h-4" />
							<a href={proposal.code_url} target="_blank" class="text-blue-600 hover:underline">
								{$_('extensions.voting.detail.view_code')}
							</a>
						</div>
					{/if}
				</div>

				<!-- Description -->
				<Card>
					<h3 class="text-lg font-semibold mb-3">{$_('extensions.voting.detail.description')}</h3>
					<p class="text-gray-700 whitespace-pre-wrap">{proposal.description}</p>
				</Card>

				<!-- Code Information -->
				<Card>
					<h3 class="text-lg font-semibold mb-3 flex items-center gap-2">
						<CodeBranchOutline class="w-5 h-5" />
						{$_('extensions.voting.detail.code_info')}
					</h3>
					
					<div class="space-y-3">
						<div>
							<div class="block text-sm font-medium text-gray-700 mb-1">
								{$_('extensions.voting.detail.code_url')}
							</div>
							<div class="flex items-center gap-2">
								<code class="bg-gray-100 px-2 py-1 rounded text-sm flex-1 break-all">
									{proposal.code_url}
								</code>
								<Button 
									size="xs" 
									color="light"
									href={proposal.code_url}
									target="_blank"
									rel="noopener noreferrer"
								>
									<LinkOutline class="w-3 h-3 mr-1" />
									{$_('extensions.voting.detail.view_code')}
								</Button>
							</div>
						</div>
						
						<div>
							<div class="block text-sm font-medium text-gray-700 mb-1">
								{$_('extensions.voting.detail.checksum')}
							</div>
							<code class="bg-gray-100 px-2 py-1 rounded text-sm block break-all">
								{proposal.code_checksum}
							</code>
						</div>
					</div>
				</Card>

				<!-- Voting Information -->
				{#if proposal.status === 'voting' || proposal.total_voters > 0}
					<Card>
						<h3 class="text-lg font-semibold mb-3">{$_('extensions.voting.detail.voting_info')}</h3>
						
						<div class="grid grid-cols-2 gap-4 mb-4">
							<div class="text-center">
								<div class="text-2xl font-bold text-green-600">{proposal.votes.yes}</div>
								<div class="text-sm text-gray-600">{$_('extensions.voting.votes.yes')}</div>
							</div>
							<div class="text-center">
								<div class="text-2xl font-bold text-red-600">{proposal.votes.no}</div>
								<div class="text-sm text-gray-600">{$_('extensions.voting.votes.no')}</div>
							</div>
							<div class="text-center">
								<div class="text-2xl font-bold text-gray-600">{proposal.votes.abstain}</div>
								<div class="text-sm text-gray-600">{$_('extensions.voting.votes.abstain')}</div>
							</div>
							<div class="text-center">
								<div class="text-2xl font-bold text-blue-600">{proposal.total_voters}</div>
								<div class="text-sm text-gray-600">{$_('extensions.voting.total_votes')}</div>
							</div>
						</div>
						
						{#if proposal.total_voters > 0}
							<div class="mb-4">
								<div class="flex justify-between text-sm text-gray-600 mb-1">
									<span>{$_('extensions.voting.approval_progress')}</span>
									<span>{((proposal.votes.yes / proposal.total_voters) * 100).toFixed(1)}%</span>
								</div>
								<div class="w-full bg-gray-200 rounded-full h-3">
									<div 
										class="bg-green-600 h-3 rounded-full transition-all duration-300" 
										style="width: {(proposal.votes.yes / proposal.total_voters) * 100}%"
									></div>
								</div>
								<div class="text-xs text-gray-500 mt-1">
									{$_('extensions.voting.threshold_required')}: {(proposal.required_threshold * 100).toFixed(0)}%
								</div>
							</div>
						{/if}
						
						{#if proposal.status === 'voting'}
							<VotingCard 
								{proposal}
								on:vote={handleVote}
							/>
						{/if}
					</Card>
				{/if}

				<!-- Demo Feature: Approve & Execute -->
				{#if proposal.status === 'voting' || proposal.status === 'accepted'}
					<Card class="border-2 border-blue-200 bg-blue-50">
						<div class="flex items-center justify-between mb-3">
							<h3 class="text-lg font-semibold text-blue-800">{$_('extensions.voting.demo_feature.title')}</h3>
							<Badge color="blue">{$_('extensions.voting.demo_feature.badge')}</Badge>
						</div>
						<p class="text-sm text-blue-700 mb-4">
							{$_('extensions.voting.demo_feature.description')}
						</p>
						
						{#if actionError}
							<Alert color="red" class="mb-3">
								<span class="font-medium">{$_('extensions.voting.error')}</span> {actionError}
							</Alert>
						{/if}
						
						{#if actionSuccess}
							<Alert color="green" class="mb-3">
								<CheckCircleSolid class="w-4 h-4 mr-2 inline" />
								<span class="font-medium">{actionSuccess}</span>
							</Alert>
						{/if}
						
						<div class="flex gap-3">
							{#if proposal.status === 'voting'}
								<Button 
									color="green"
									on:click={handleApprove}
									disabled={approving || executing}
								>
									{#if approving}
										<Spinner size="4" class="mr-2" />
										{$_('extensions.voting.demo_feature.approving')}
									{:else}
										<CheckCircleSolid class="w-4 h-4 mr-2" />
										{$_('extensions.voting.demo_feature.approve')}
									{/if}
								</Button>
							{/if}
							
							{#if proposal.status === 'accepted'}
								<Button 
									color="purple"
									on:click={handleExecute}
									disabled={approving || executing}
								>
									{#if executing}
										<Spinner size="4" class="mr-2" />
										{$_('extensions.voting.demo_feature.executing')}
									{:else}
										<PlaySolid class="w-4 h-4 mr-2" />
										{$_('extensions.voting.demo_feature.execute')}
									{/if}
								</Button>
							{/if}
						</div>
					</Card>
				{/if}

				<!-- Security Warning -->
				<Alert color="yellow">
					<span class="font-medium">{$_('extensions.voting.detail.security_warning.title')}</span>
					{$_('extensions.voting.detail.security_warning.message')}
				</Alert>
			</div>

			<!-- Right Column: Code Viewer -->
			<div class="bg-gray-50 rounded-lg border overflow-hidden flex flex-col">
				<div class="bg-gray-100 px-4 py-2 border-b flex items-center justify-between">
					<div class="flex items-center gap-2">
						<CodeBranchOutline class="w-4 h-4 text-gray-600" />
						<h3 class="font-semibold text-gray-800">{$_('extensions.voting.detail.code_content')}</h3>
					</div>
					<span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
						{proposal.code_url ? proposal.code_url.split('/').pop() : 'proposal.py'}
					</span>
				</div>
				
				<div class="p-4 flex-1 overflow-y-auto max-h-[70vh]">
					{#if codeLoading}
						<div class="flex items-center justify-center py-8">
							<Spinner size="8" />
							<span class="ml-3 text-gray-600">{$_('extensions.voting.loading_code')}</span>
						</div>
					{:else if codeError}
						<Alert color="red" class="mb-4">
							<span class="font-medium">{$_('extensions.voting.error')}</span> {codeError}
						</Alert>
						<div class="text-center">
							<Button size="sm" color="light" on:click={fetchCode}>
								{$_('extensions.voting.retry')}
							</Button>
						</div>
					{:else if codeContent}
						<div class="font-mono text-sm">
							<!-- Code with line numbers -->
							<div class="bg-gray-900 rounded-lg overflow-hidden">
								<pre class="p-4 overflow-x-auto"><code class="text-gray-100">{codeContent}</code></pre>
							</div>
							
							<!-- Checksum display -->
							{#if codeChecksum}
								<div class="mt-4 pt-3 border-t border-gray-200">
									<div class="text-xs text-gray-500">
										<div class="flex justify-between items-center">
											<span class="font-medium">{$_('extensions.voting.detail.checksum')}:</span>
											<code class="bg-gray-100 px-2 py-1 rounded text-xs break-all ml-2">
												{codeChecksum}
											</code>
										</div>
										<div class="flex justify-between mt-2">
											<span>{$_('extensions.voting.lines')}:</span>
											<span class="font-medium">{codeContent.split('\n').length}</span>
										</div>
									</div>
								</div>
							{/if}
						</div>
					{:else}
						<div class="text-center py-8 text-gray-500">
							{$_('extensions.voting.no_code')}
						</div>
					{/if}
				</div>
			</div>
</div>
