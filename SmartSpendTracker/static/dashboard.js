// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons
    feather.replace();
    
    // API endpoint
    const API_URL = '/api';
    
    // DOM elements
    const expensesList = document.getElementById('expensesList');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const noDataMessage = document.getElementById('noDataMessage');
    const totalExpenses = document.getElementById('totalExpenses');
    const receiptCount = document.getElementById('receiptCount');
    const averagePrice = document.getElementById('averagePrice');
    const expenseChart = document.getElementById('expenseChart');
    const priceDistribution = document.getElementById('priceDistribution');
    const topItemsList = document.getElementById('topItemsList');
    
    // Show loading spinner
    loadingSpinner.classList.remove('d-none');
    
    // Fetch expense data
    fetchExpenseData();
    
    /**
     * Fetch expense data from API
     */
    async function fetchExpenseData() {
        try {
            const response = await fetch(`${API_URL}/receipt-items`);
            
            if (!response.ok) {
                throw new Error('Failed to fetch expense data');
            }
            
            const data = await response.json();
            
            // Hide loading spinner
            loadingSpinner.classList.add('d-none');
            
            if (data.length === 0) {
                // Show no data message
                noDataMessage.classList.remove('d-none');
            } else {
                // Process and display data
                processExpenseData(data);
            }
            
        } catch (error) {
            console.error('Error fetching expense data:', error);
            
            // Hide loading spinner
            loadingSpinner.classList.add('d-none');
            
            // Show error message
            noDataMessage.classList.remove('d-none');
            noDataMessage.querySelector('h5').textContent = 'Error Loading Data';
            noDataMessage.querySelector('p').textContent = 'Failed to load expense data. Please try again.';
        }
    }
    
    /**
     * Process and display expense data
     */
    function processExpenseData(data) {
        // Calculate summary statistics
        const total = data.reduce((sum, item) => sum + item.price, 0);
        const uniqueReceipts = new Set(data.map(item => {
            // Extract date part for rough receipt count estimation
            // This is an approximation since we don't have actual receipt IDs
            return item.created_at ? item.created_at.split('T')[0] : 'unknown';
        })).size;
        const avg = total / data.length;
        
        // Update summary cards
        totalExpenses.textContent = `$${total.toFixed(2)}`;
        receiptCount.textContent = uniqueReceipts;
        averagePrice.textContent = `$${avg.toFixed(2)}`;
        
        // Populate expense table
        populateExpenseTable(data);
        
        // Display top 5 items
        displayTopItems(data);
        
        // Create charts
        createExpenseChart(data);
        createPriceDistributionChart(data);
    }
    
    /**
     * Display top 5 items by price
     */
    function displayTopItems(data) {
        // Sort data by price (highest first)
        const sortedData = [...data].sort((a, b) => b.price - a.price);
        
        // Take top 5 items
        const topItems = sortedData.slice(0, 5);
        
        // Clear existing items
        topItemsList.innerHTML = '';
        
        if (topItems.length === 0) {
            const listItem = document.createElement('li');
            listItem.className = 'list-group-item bg-transparent d-flex justify-content-between';
            listItem.innerHTML = `
                <span>No items yet</span>
                <span class="badge bg-primary rounded-pill">$0.00</span>
            `;
            topItemsList.appendChild(listItem);
            return;
        }
        
        // Add items to the list
        topItems.forEach(item => {
            const listItem = document.createElement('li');
            listItem.className = 'list-group-item bg-transparent d-flex justify-content-between align-items-center';
            
            const itemName = document.createElement('span');
            // Truncate long item names
            itemName.textContent = item.item.length > 20 ? item.item.substring(0, 18) + '...' : item.item;
            itemName.title = item.item; // Full name on hover
            
            const priceTag = document.createElement('span');
            priceTag.className = 'badge bg-primary rounded-pill';
            priceTag.textContent = `$${item.price.toFixed(2)}`;
            
            listItem.appendChild(itemName);
            listItem.appendChild(priceTag);
            
            topItemsList.appendChild(listItem);
        });
    }
    
    /**
     * Populate expense table with data
     */
    function populateExpenseTable(data) {
        // Sort data by created_at (newest first)
        const sortedData = [...data].sort((a, b) => {
            return new Date(b.created_at || 0) - new Date(a.created_at || 0);
        });
        
        // Clear existing rows
        expensesList.innerHTML = '';
        
        // Add rows for each expense
        sortedData.forEach(item => {
            const row = document.createElement('tr');
            
            // ID cell
            const idCell = document.createElement('td');
            idCell.textContent = item.id;
            
            // Item cell
            const itemCell = document.createElement('td');
            itemCell.textContent = item.item;
            
            // Price cell
            const priceCell = document.createElement('td');
            priceCell.textContent = `$${item.price.toFixed(2)}`;
            priceCell.className = 'text-end';
            
            // Date cell
            const dateCell = document.createElement('td');
            if (item.created_at) {
                const date = new Date(item.created_at);
                dateCell.textContent = date.toLocaleDateString();
            } else {
                dateCell.textContent = 'N/A';
            }
            
            // Category cell
            const categoryCell = document.createElement('td');
            if (item.category) {
                const categoryBadge = document.createElement('span');
                categoryBadge.className = 'badge rounded-pill';
                categoryBadge.style.backgroundColor = item.category.color;
                categoryBadge.textContent = item.category.name;
                categoryCell.appendChild(categoryBadge);
            } else {
                categoryCell.textContent = 'Uncategorized';
            }
            
            // Actions cell
            const actionsCell = document.createElement('td');
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'btn-group btn-group-sm';
            
            const categoryBtn = document.createElement('a');
            categoryBtn.href = `/categorize/${item.id}`;
            categoryBtn.className = 'btn btn-outline-primary';
            categoryBtn.innerHTML = '<i data-feather="tag" style="width: 16px; height: 16px;"></i>';
            categoryBtn.title = 'Categorize';
            
            actionsDiv.appendChild(categoryBtn);
            actionsCell.appendChild(actionsDiv);
            
            // Add cells to row
            row.appendChild(idCell);
            row.appendChild(itemCell);
            row.appendChild(priceCell);
            row.appendChild(categoryCell);
            row.appendChild(dateCell);
            row.appendChild(actionsCell);
            
            // Add row to table
            expensesList.appendChild(row);
        });
    }
    
    /**
     * Create expense trend chart
     */
    function createExpenseChart(data) {
        // Group data by date
        const dateGroups = data.reduce((groups, item) => {
            if (!item.created_at) return groups;
            
            const date = item.created_at.split('T')[0]; // Get date part only
            if (!groups[date]) {
                groups[date] = 0;
            }
            groups[date] += item.price;
            return groups;
        }, {});
        
        // Sort dates
        const sortedDates = Object.keys(dateGroups).sort();
        
        // Prepare chart data
        const chartLabels = sortedDates.map(date => {
            const d = new Date(date);
            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
        
        const chartData = sortedDates.map(date => dateGroups[date]);
        
        // Create chart
        new Chart(expenseChart, {
            type: 'line',
            data: {
                labels: chartLabels,
                datasets: [{
                    label: 'Daily Expenses',
                    data: chartData,
                    borderColor: '#3e95cd',
                    backgroundColor: 'rgba(62, 149, 205, 0.1)',
                    borderWidth: 2,
                    tension: 0.2,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,  // Fixed aspect ratio
                animation: {
                    duration: 500 // Reduced animation duration
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `$${context.raw.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value;
                            },
                            maxTicksLimit: 6 // Limit Y-axis ticks
                        },
                        grace: '5%' // Add padding to the scale
                    },
                    x: {
                        ticks: {
                            maxTicksLimit: 7 // Limit X-axis ticks to prevent overcrowding
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Create price distribution chart
     */
    function createPriceDistributionChart(data) {
        // Create price ranges
        const ranges = {
            '< $5': 0,
            '$5 - $10': 0,
            '$10 - $20': 0,
            '$20 - $50': 0,
            '$50+': 0
        };
        
        // Count items in each range
        data.forEach(item => {
            if (item.price < 5) {
                ranges['< $5']++;
            } else if (item.price < 10) {
                ranges['$5 - $10']++;
            } else if (item.price < 20) {
                ranges['$10 - $20']++;
            } else if (item.price < 50) {
                ranges['$20 - $50']++;
            } else {
                ranges['$50+']++;
            }
        });
        
        // Create chart
        new Chart(priceDistribution, {
            type: 'doughnut',
            data: {
                labels: Object.keys(ranges),
                datasets: [{
                    data: Object.values(ranges),
                    backgroundColor: [
                        '#4dc9f6',
                        '#f67019',
                        '#f53794',
                        '#537bc4',
                        '#acc236'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${value} items (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
});