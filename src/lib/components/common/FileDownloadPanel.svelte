<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { formatFileSize } from '$lib/utils';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

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

{#if files.length > 0}
	<div class="flex justify-start pb-1">
		<div class="rounded-3xl max-w-[90%] px-5 py-2 bg-gray-50 dark:bg-gray-850">
			<div class="space-y-3">
				{#each displayFiles as file (file.id || file.name)}
					<div class="flex items-center gap-3">
						<!-- File Icon -->
						<div
							class="flex-shrink-0 w-8 h-8 {getFileTypeInfo(file)
								.bgColor} rounded-lg flex items-center justify-center"
						>
							<span class="text-sm">{getFileTypeInfo(file).icon}</span>
						</div>

						<!-- File Info -->
						<button
							on:click={() => handleFileClick(file)}
							class="min-w-0 text-left hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg p-1 -m-1 transition-colors"
						>
							<h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
								{file.name}
							</h4>

							<div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
								{#if file.size}
									<span>{formatFileSize(file.size)}</span>
									<span>•</span>
								{/if}
								<span class="font-medium {getFileTypeInfo(file).color}">
									{file.format || 'Unknown'}
								</span>
							</div>
						</button>

						<!-- Download Button -->
						<a
							href="#"
							class="inline-flex items-center gap-1 px-2 py-1 bg-green-500 hover:bg-green-600 text-white text-xs font-medium rounded-lg transition-colors"
							title={$i18n.t('Download {{fileName}}', { fileName: file.name })}
							on:click|preventDefault={() => {
								if (file.id) {
									window.open(`${WEBUI_API_BASE_URL}/files/${file.id}/content`, '_blank');
								}
							}}
						>
							<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
								></path>
							</svg>
							<span>{$i18n.t('Download')}</span>
						</a>
					</div>
				{/each}
			</div>

			<!-- Show More Button -->
			{#if hasMoreFiles}
				<button
					on:click={() => (maxDisplayFiles += 10)}
					class="w-full mt-3 py-1 text-xs text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 rounded-lg hover:bg-green-100 dark:hover:bg-green-900 transition-colors"
				>
					{$i18n.t('Show {{count}} more files', { count: files.length - maxDisplayFiles })}
				</button>
			{/if}
		</div>
	</div>
{/if}
