// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons
    feather.replace();
    
    // Get DOM elements
    const fileInput = document.getElementById('fileInput');
    const dropZone = document.getElementById('dropZone');
    const browseButton = document.getElementById('browseButton');
    const uploadButton = document.getElementById('uploadButton');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const removeFile = document.getElementById('removeFile');
    const processingStatus = document.getElementById('processingStatus');
    const statusMessage = document.getElementById('statusMessage');
    const resultsCard = document.getElementById('resultsCard');
    const errorCard = document.getElementById('errorCard');
    const errorMessage = document.getElementById('errorMessage');
    const tryAgainButton = document.getElementById('tryAgainButton');
    const itemsList = document.getElementById('itemsList');
    const itemsCount = document.getElementById('itemsCount');
    const totalPrice = document.getElementById('totalPrice');
    
    // API endpoint
    const API_URL = '/api';
    
    // Event listeners for file upload
    browseButton.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop handlers
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('highlight');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('highlight');
    });
    
    dropZone.addEventListener('drop', handleFileDrop);
    
    // Remove file button
    removeFile.addEventListener('click', resetFileInput);
    
    // Upload button
    uploadButton.addEventListener('click', uploadReceipt);
    
    // Try again button
    tryAgainButton.addEventListener('click', () => {
        errorCard.classList.add('d-none');
        resetFileInput();
    });
    
    /**
     * Handle file selection from input
     */
    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            validateAndPreviewFile(file);
        }
    }
    
    /**
     * Handle file drop
     */
    function handleFileDrop(e) {
        e.preventDefault();
        dropZone.classList.remove('highlight');
        
        if (e.dataTransfer.files.length) {
            const file = e.dataTransfer.files[0];
            validateAndPreviewFile(file);
            
            // Update the file input to maintain consistency
            fileInput.files = e.dataTransfer.files;
        }
    }
    
    /**
     * Validate and preview selected file
     */
    function validateAndPreviewFile(file) {
        // Check if file is an image
        if (!file.type.startsWith('image/')) {
            showError('Please upload an image file (PNG, JPG, etc.)');
            resetFileInput();
            return;
        }
        
        // Check file size (5MB limit)
        if (file.size > 5 * 1024 * 1024) {
            showError('File size exceeds 5MB limit');
            resetFileInput();
            return;
        }
        
        // Display file info
        fileName.textContent = file.name;
        fileInfo.classList.remove('d-none');
        uploadButton.disabled = false;
    }
    
    /**
     * Reset file input and related UI
     */
    function resetFileInput() {
        fileInput.value = '';
        fileName.textContent = 'No file selected';
        fileInfo.classList.add('d-none');
        uploadButton.disabled = true;
    }
    
    /**
     * Upload and process receipt
     */
    async function uploadReceipt() {
        if (!fileInput.files.length) {
            return;
        }
        
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        // Show processing status
        processingStatus.classList.remove('d-none');
        uploadButton.disabled = true;
        statusMessage.textContent = 'Processing your receipt...';
        
        // Hide any previous results/errors
        resultsCard.classList.add('d-none');
        errorCard.classList.add('d-none');
        
        try {
            const response = await fetch(`${API_URL}/upload-receipt/`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error processing receipt');
            }
            
            const data = await response.json();
            displayResults(data);
            
        } catch (error) {
            console.error('Upload error:', error);
            showError(error.message || 'Failed to process receipt');
        } finally {
            processingStatus.classList.add('d-none');
        }
    }
    
    /**
     * Display OCR results
     */
    function displayResults(data) {
        // Hide processing status
        processingStatus.classList.add('d-none');
        
        // Update items count
        itemsCount.textContent = data.items_found;
        
        // Clear previous items
        itemsList.innerHTML = '';
        
        // No items found
        if (data.items_found === 0) {
            showError('No items detected in the receipt. Please try again with a clearer image.');
            return;
        }
        
        // Calculate total price
        let total = 0;
        
        // Add items to the list
        data.items.forEach(item => {
            const row = document.createElement('tr');
            
            const itemCell = document.createElement('td');
            itemCell.textContent = item.item;
            
            const priceCell = document.createElement('td');
            priceCell.textContent = `$${item.price.toFixed(2)}`;
            priceCell.className = 'text-end';
            
            row.appendChild(itemCell);
            row.appendChild(priceCell);
            
            itemsList.appendChild(row);
            
            // Add to total
            total += item.price;
        });
        
        // Update total price
        totalPrice.textContent = `$${total.toFixed(2)}`;
        
        // Show results card
        resultsCard.classList.remove('d-none');
    }
    
    /**
     * Show error message
     */
    function showError(message) {
        errorMessage.textContent = message;
        errorCard.classList.remove('d-none');
        processingStatus.classList.add('d-none');
    }
});
