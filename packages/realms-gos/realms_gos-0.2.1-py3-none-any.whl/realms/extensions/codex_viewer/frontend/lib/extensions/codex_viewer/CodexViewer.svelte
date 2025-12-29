<script lang="ts">
  import { onMount } from 'svelte';
  import { _ } from 'svelte-i18n';
  import { goto } from '$app/navigation';
  import { backend } from '$lib/canisters';
  import { Button, Badge, Card, Spinner, Input } from 'flowbite-svelte';

  interface Codex {
    _id: string;
    name: string;
    description: string;
    code_preview: string;
    created_at: number | null;
    updated_at: number | null;
  }

  let codexes: Codex[] = [];
  let loading = true;
  let error = '';
  let searchTerm = '';

  $: filteredCodexes = codexes.filter(codex => {
    const term = searchTerm.toLowerCase();
    return !searchTerm || 
      codex.name.toLowerCase().includes(term) ||
      codex.description?.toLowerCase().includes(term);
  });

  onMount(() => {
    loadCodexes();
  });

  async function loadCodexes() {
    loading = true;
    error = '';
    
    try {
      const response = await backend.extension_sync_call({
        extension_name: 'codex_viewer',
        function_name: 'get_all_codexes',
        args: '{}'
      });
      
      if (response.success) {
        const data = typeof response.response === 'string' ? JSON.parse(response.response) : response.response;
        if (data.success !== false) {
          codexes = data.codexes || [];
        } else {
          error = data.error || 'Failed to load codexes';
        }
      } else {
        error = response.error || 'Failed to load codexes';
      }
    } catch (e: any) {
      error = e.message || 'Error loading codexes';
    } finally {
      loading = false;
    }
  }

  function viewCodex(codexId: string) {
    goto(`/extensions/codex_viewer/${codexId}`);
  }

  function formatTimestamp(timestamp: number | null): string {
    if (!timestamp) return '-';
    return new Date(timestamp / 1000000).toLocaleString();
  }
</script>

<div class="p-6 max-w-6xl mx-auto">
  <!-- Header -->
  <div class="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
    <div>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {$_('extensions.codex_viewer.title')}
      </h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
        {$_('extensions.codex_viewer.subtitle')}
      </p>
    </div>
    <Button on:click={loadCodexes} size="sm" color="light">
      <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
      </svg>
      {$_('extensions.codex_viewer.refresh')}
    </Button>
  </div>

  {#if error}
    <div class="mb-4 p-4 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-200 rounded-lg">
      {error}
    </div>
  {/if}

  {#if loading}
    <div class="flex justify-center items-center py-16">
      <Spinner size="12" />
    </div>
  {:else}
    <!-- Search -->
    <div class="mb-6">
      <Input 
        placeholder={$_('extensions.codex_viewer.search_placeholder')}
        bind:value={searchTerm}
        class="max-w-md"
      >
        <svg slot="left" class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
      </Input>
    </div>

    <!-- Stats -->
    <div class="mb-6 flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
      <span>{codexes.length} {$_('extensions.codex_viewer.total_codexes')}</span>
      {#if searchTerm && filteredCodexes.length !== codexes.length}
        <span>({filteredCodexes.length} {$_('extensions.codex_viewer.matching')})</span>
      {/if}
    </div>

    {#if filteredCodexes.length === 0}
      <Card class="text-center py-12">
        <svg class="w-12 h-12 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/>
        </svg>
        <p class="text-gray-500 dark:text-gray-400">
          {$_('extensions.codex_viewer.no_codexes')}
        </p>
      </Card>
    {:else}
      <!-- Codex Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {#each filteredCodexes as codex}
          <button
            class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 text-left hover:shadow-lg hover:border-blue-300 dark:hover:border-blue-600 transition-all duration-200 cursor-pointer"
            on:click={() => viewCodex(codex._id)}
          >
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-2">
                <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/>
                </svg>
                <h3 class="font-semibold text-gray-900 dark:text-white truncate">
                  {codex.name}
                </h3>
              </div>
              <Badge color="blue" class="text-xs">Python</Badge>
            </div>
            
            {#if codex.description}
              <p class="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                {codex.description}
              </p>
            {/if}
            
            {#if codex.code_preview}
              <div class="bg-gray-900 rounded p-2 mb-3 overflow-hidden">
                <pre class="text-xs text-gray-300 font-mono truncate">{codex.code_preview.split('\n').slice(0, 3).join('\n')}</pre>
              </div>
            {/if}
            
            <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-500">
              <span>ID: {codex._id.substring(0, 8)}</span>
              <span class="text-blue-600 dark:text-blue-400 hover:underline">
                View Code →
              </span>
            </div>
          </button>
        {/each}
      </div>
    {/if}
  {/if}
</div>

<style>
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
