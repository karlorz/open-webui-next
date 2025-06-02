import { WEBUI_API_BASE_URL } from '$lib/constants';

export const uploadFile = async (token: string, file: File, metadata?: object | null) => {
	const data = new FormData();
	data.append('file', file);
	if (metadata) {
		data.append('metadata', JSON.stringify(metadata));
	}

	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			authorization: `Bearer ${token}`
		},
		body: data
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const uploadDir = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/upload/dir`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getFiles = async (token: string = '', chatId?: string, generatedBy?: string) => {
	let error = null;

	// Build query parameters for filtering
	const params = new URLSearchParams();
	if (chatId) params.append('chat_id', chatId);
	if (generatedBy) params.append('generated_by', generatedBy);

	const queryString = params.toString();
	const url = `${WEBUI_API_BASE_URL}/files/${queryString ? '?' + queryString : ''}`;

	const res = await fetch(url, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getFileById = async (token: string, id: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/${id}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updateFileDataContentById = async (token: string, id: string, content: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/${id}/data/content/update`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			content: content
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getFileContentById = async (id: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/${id}/content`, {
		method: 'GET',
		headers: {
			Accept: 'application/json'
		},
		credentials: 'include'
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return await res.blob();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);

			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const deleteFileById = async (token: string, id: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/${id}`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const deleteAllFiles = async (token: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/all`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

// Simplified function that uses existing file download system
export const downloadFileById = async (token: string, fileId: string, filename?: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/files/${fileId}/content?attachment=true`, {
		method: 'GET',
		headers: {
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res;
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	// If successful, trigger download
	if (res) {
		const blob = await res.blob();
		const contentDisposition = res.headers.get('Content-Disposition');
		let downloadFilename = filename; // Use provided filename if available

		// Extract filename from Content-Disposition header (backend should provide this)
		if (contentDisposition) {
			const filenameMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)/);
			if (filenameMatch) {
				downloadFilename = decodeURIComponent(filenameMatch[1]);
			} else {
				const simpleFilenameMatch = contentDisposition.match(/filename="([^"]+)"/);
				if (simpleFilenameMatch) {
					downloadFilename = simpleFilenameMatch[1];
				}
			}
		}

		// Fallback to file ID if no filename found anywhere
		if (!downloadFilename) {
			downloadFilename = `file_${fileId}`;
			console.warn(`No filename found for file ${fileId}, using fallback: ${downloadFilename}`);
		}

		const url = window.URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = downloadFilename;
		document.body.appendChild(a);
		a.click();
		window.URL.revokeObjectURL(url);
		document.body.removeChild(a);
	}

	return res;
};

// Convenience functions using the enhanced getFiles function
export const getCodeGeneratedFiles = async (token: string, chatId: string) => {
	return getFiles(token, chatId, 'code_interpreter');
};

export const getDownloadableFiles = async (token: string, chatId?: string) => {
	// Get files with downloadable extensions
	const files = await getFiles(token, chatId);
	if (!files) return null;

	const downloadableExtensions = [
		'.xlsx',
		'.xls',
		'.csv',
		'.pdf',
		'.png',
		'.jpg',
		'.jpeg',
		'.gif',
		'.txt',
		'.json'
	];
	return files.filter((file: any) => {
		const filename = file.filename || file.meta?.name || '';
		return downloadableExtensions.some((ext) => filename.toLowerCase().endsWith(ext));
	});
};

// Use existing download function for code-generated files
export const downloadCodeGeneratedFile = async (
	token: string,
	fileId: string,
	filename?: string
) => {
	return downloadFileById(token, fileId, filename);
};
