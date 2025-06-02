<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { formatFileSize } from '$lib/utils';
	import { downloadCodeGeneratedFile } from '$lib/apis/files';
	import { toast } from 'svelte-sonner';

	import Spinner from './Spinner.svelte';
	import Tooltip from './Tooltip.svelte';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let files = [];
	export let title = 'Generated Files';
	export let subtitle = 'Files created during code execution';
	export let loading = false;
	export let showRefreshButton = true;
	export let maxDisplayFiles = 10;

	let downloadingFiles = new Set();

	// File type icons and colors
	const getFileTypeInfo = (file) => {
		const ext = file.format?.toLowerCase() || file.name?.split('.').pop()?.toLowerCase();

		const typeMap = {
			excel: { icon: '📊', color: 'text-green-600', bgColor: 'bg-green-100 dark:bg-green-900' },
			xlsx: { icon: '📊', color: 'text-green-600', bgColor: 'bg-green-100 dark:bg-green-900' },
			xls: { icon: '📊', color: 'text-green-600', bgColor: 'bg-green-100 dark:bg-green-900' },
			csv: { icon: '📋', color: 'text-blue-600', bgColor: 'bg-blue-100 dark:bg-blue-900' },
			pdf: { icon: '📑', color: 'text-red-600', bgColor: 'bg-red-100 dark:bg-red-900' },
			image: { icon: '🖼️', color: 'text-purple-600', bgColor: 'bg-purple-100 dark:bg-purple-900' },
			text: { icon: '📄', color: 'text-gray-600', bgColor: 'bg-gray-100 dark:bg-gray-900' }
		};

		return typeMap[ext] || typeMap['text'];
	};

	const handleDownload = async (file) => {
		downloadingFiles.add(file.id);
		downloadingFiles = downloadingFiles; // Trigger reactivity

		try {
			// Always use the unified API server for all downloads, pass the filename
			if (file.id) {
				await downloadCodeGeneratedFile(localStorage.token, file.id, file.name);
				toast.success($i18n.t('Downloaded {{fileName}}', { fileName: file.name }));
			} else {
				// Fallback warning for files without proper ID
				console.warn('File missing ID, cannot download via API:', file);
				toast.error($i18n.t('Cannot download file: Missing file ID'));
				return;
			}

			dispatch('downloaded', file);
		} catch (error) {
			console.error('Download error:', error);
			toast.error(
				$i18n.t('Failed to download {{fileName}}: {{error}}', {
					fileName: file.name,
					error: error.message || 'Unknown error'
				})
			);
		} finally {
			downloadingFiles.delete(file.id);
			downloadingFiles = downloadingFiles; // Trigger reactivity
		}
	};

	const handleRefresh = () => {
		dispatch('refresh');
	};

	const handleFileClick = (file) => {
		dispatch('fileClick', file);
	};

	// Group files by type for better organization
	$: groupedFiles = files.reduce((acc, file) => {
		const ext = file.format?.toLowerCase() || file.name?.split('.').pop()?.toLowerCase();
		const category = ['xlsx', 'xls'].includes(ext)
			? 'Excel'
			: ext === 'csv'
				? 'CSV'
				: ext === 'pdf'
					? 'PDF'
					: 'Other';

		if (!acc[category]) acc[category] = [];
		acc[category].push(file);
		return acc;
	}, {});

	$: displayFiles = files.slice(0, maxDisplayFiles);
	$: hasMoreFiles = files.length > maxDisplayFiles;
</script>

{#if files.length > 0 || loading}
	<div
		class="mt-4 p-4 bg-green-50 dark:bg-green-950 rounded-xl border border-green-200 dark:border-green-800"
	>
		<!-- Header -->
		<div class="flex items-center justify-between mb-3">
			<div class="flex items-center gap-2">
				<div class="flex items-center gap-2">
					<div class="w-2 h-2 bg-green-500 rounded-full"></div>
					<h3 class="text-sm font-semibold text-green-800 dark:text-green-200">
						{title}
					</h3>
				</div>

				{#if files.length > 0}
					<span
						class="px-2 py-1 bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200 text-xs rounded-full font-medium"
					>
						{files.length}
					</span>
				{/if}
			</div>

			{#if showRefreshButton}
				<button
					on:click={handleRefresh}
					class="p-1.5 hover:bg-green-100 dark:hover:bg-green-900 rounded-lg transition-colors"
					title={$i18n.t('Refresh files')}
				>
					<svg
						class="w-4 h-4 text-green-600 dark:text-green-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
						></path>
					</svg>
				</button>
			{/if}
		</div>

		{#if subtitle}
			<p class="text-xs text-green-600 dark:text-green-400 mb-3">{subtitle}</p>
		{/if}

		<!-- Loading State -->
		{#if loading}
			<div class="flex items-center justify-center py-6">
				<Spinner className="w-5 h-5 text-green-500" />
				<span class="ml-2 text-sm text-green-600 dark:text-green-400">
					{$i18n.t('Loading files...')}
				</span>
			</div>
		{:else}
			<!-- File Grid -->
			<div class="space-y-3">
				{#each displayFiles as file (file.id || file.name)}
					<div
						class="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border border-green-100 dark:border-green-900 hover:shadow-sm transition-all duration-200 group"
					>
						<button
							on:click={() => handleFileClick(file)}
							class="flex items-center gap-3 flex-1 min-w-0 text-left hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg p-1 -m-1 transition-colors"
						>
							<!-- File Icon -->
							<div
								class="flex-shrink-0 w-10 h-10 {getFileTypeInfo(file)
									.bgColor} rounded-lg flex items-center justify-center"
							>
								<span class="text-lg">{getFileTypeInfo(file).icon}</span>
							</div>

							<!-- File Info -->
							<div class="flex-1 min-w-0">
								<Tooltip content={file.name} placement="top-start">
									<h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
										{file.name}
									</h4>
								</Tooltip>

								<div
									class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mt-0.5"
								>
									{#if file.size}
										<span>{formatFileSize(file.size)}</span>
										<span>•</span>
									{/if}
									<span class="font-medium {getFileTypeInfo(file).color}">
										{file.format || 'Unknown'}
									</span>
									{#if file.created_at}
										<span>•</span>
										<span>{new Date(file.created_at).toLocaleDateString()}</span>
									{/if}
								</div>
							</div>
						</button>

						<!-- Download Button -->
						<div class="flex-shrink-0 ml-2">
							<button
								on:click={() => handleDownload(file)}
								disabled={downloadingFiles.has(file.id)}
								class="inline-flex items-center gap-1 px-3 py-1.5 bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white text-xs font-medium rounded-lg transition-colors group-hover:shadow-sm"
								title={$i18n.t('Download {{fileName}}', { fileName: file.name })}
							>
								{#if downloadingFiles.has(file.id)}
									<Spinner className="w-3 h-3" />
								{:else}
									<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
										></path>
									</svg>
								{/if}
								<span>{$i18n.t('Download')}</span>
							</button>
						</div>
					</div>
				{/each}
			</div>

			<!-- Show More Button -->
			{#if hasMoreFiles}
				<button
					on:click={() => (maxDisplayFiles += 10)}
					class="w-full mt-3 py-2 text-sm text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 border border-green-200 dark:border-green-800 rounded-lg hover:bg-green-100 dark:hover:bg-green-900 transition-colors"
				>
					{$i18n.t('Show {{count}} more files', { count: files.length - maxDisplayFiles })}
				</button>
			{/if}

			<!-- Category Summary (when many files) -->
			{#if files.length > 5}
				<div class="mt-3 flex flex-wrap gap-2">
					{#each Object.entries(groupedFiles) as [category, categoryFiles]}
						<span
							class="px-2 py-1 bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200 text-xs rounded-full"
						>
							{category}: {categoryFiles.length}
						</span>
					{/each}
				</div>
			{/if}

			<!-- Helper Text -->
			<div class="mt-3 text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
				<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
					></path>
				</svg>
				{$i18n.t('Files are automatically saved when you request Excel, CSV, or PDF formats')}
			</div>
		{/if}
	</div>
{/if}

<style>
	/* Custom scrollbar for file list if needed */
	.space-y-3 {
		max-height: 400px;
		overflow-y: auto;
	}

	.space-y-3::-webkit-scrollbar {
		width: 4px;
	}

	.space-y-3::-webkit-scrollbar-track {
		background: transparent;
	}

	.space-y-3::-webkit-scrollbar-thumb {
		background: rgba(34, 197, 94, 0.3);
		border-radius: 2px;
	}

	.space-y-3::-webkit-scrollbar-thumb:hover {
		background: rgba(34, 197, 94, 0.5);
	}
</style>
