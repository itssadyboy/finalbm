// Global variables
let productionItems = [];
let saleItems = [];

// Document ready
$(document).ready(function() {
    initMasters();
    initEntries();
    initHelp();
});

// Masters management
function initMasters() {
    // Operators form
    $('#operatorForm').on('submit', function(e) {
        e.preventDefault();
        const data = {
            name: $('#opName').val(),
            mobile: $('#opMobile').val(),
            address: $('#opAddress').val()
        };
        
        if (!data.name) {
            alert('Operator name is required');
            return;
        }
        
        addMaster('operators', data, '#operatorForm');
    });
    
    // Parties form
    $('#partyForm').on('submit', function(e) {
        e.preventDefault();
        const data = {
            name: $('#ptName').val(),
            mobile: $('#ptMobile').val(),
            address: $('#ptAddress').val()
        };
        
        if (!data.name) {
            alert('Party name is required');
            return;
        }
        
        addMaster('parties', data, '#partyForm');
    });
    
    // Machines form
    $('#machineForm').on('submit', function(e) {
        e.preventDefault();
        const data = {
            name: $('#mcName').val(),
            remarks: $('#mcRemarks').val()
        };
        
        if (!data.name) {
            alert('Machine name is required');
            return;
        }
        
        addMaster('machines', data, '#machineForm');
    });
    
    // Items form
    $('#itemForm').on('submit', function(e) {
        e.preventDefault();
        const data = {
            name: $('#itName').val(),
            type: $('#itType').val()
        };
        
        if (!data.name) {
            alert('Item name is required');
            return;
        }
        
        addMaster('items', data, '#itemForm');
    });
    
    // Delete master records
    $(document).on('click', '.delete-btn', function() {
        const table = $(this).data('table');
        const id = $(this).data('id');
        const name = $(this).closest('tr').find('td:nth-child(2)').text();
        
        if (confirm(`Are you sure you want to delete "${name}"?`)) {
            deleteMaster(table, id);
        }
    });
}

function addMaster(table, data, formSelector) {
    $.ajax({
        url: '/api/add_master',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ table, data }),
        success: function(response) {
            if (response.success) {
                alert(response.message);
                $(formSelector)[0].reset();
                location.reload();
            } else {
                alert(response.message);
            }
        },
        error: function() {
            alert('Error adding record');
        }
    });
}

function deleteMaster(table, id) {
    $.ajax({
        url: '/api/delete_master',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ table, id }),
        success: function(response) {
            if (response.success) {
                alert(response.message);
                location.reload();
            }
        },
        error: function() {
            alert('Error deleting record');
        }
    });
}

// Entries management
function initEntries() {
    // Production entries
    $('#addProdItem').on('click', function() {
        const itemId = $('#prodItem').val();
        const machineId = $('#prodMachine').val();
        const length = $('#prodLength').val();
        const weight = $('#prodWeight').val();
        const remarks = $('#prodRemarks').val();
        
        if (!itemId || !machineId) {
            alert('Please select both item and machine');
            return;
        }
        
        const itemName = $('#prodItem option:selected').text();
        const machineName = $('#prodMachine option:selected').text();
        
        const item = {
            item_id: parseInt(itemId),
            item_name: itemName,
            machine_id: parseInt(machineId),
            machine_name: machineName,
            length: parseFloat(length) || 0,
            weight: parseFloat(weight) || 0,
            remarks: remarks
        };
        
        productionItems.push(item);
        updateProductionItemsTable();
        
        // Clear form
        $('#prodLength, #prodWeight, #prodRemarks').val('');
    });
    
    // Sale entries
    $('#addSaleItem').on('click', function() {
        const itemId = $('#saleItem').val();
        const quantity = $('#saleQuantity').val();
        const rate = $('#saleRate').val();
        const amount = $('#saleAmount').val();
        const remarks = $('#saleRemarks').val();
        
        if (!itemId) {
            alert('Please select an item');
            return;
        }
        
        const itemName = $('#saleItem option:selected').text();
        
        const item = {
            item_id: parseInt(itemId),
            item_name: itemName,
            quantity: parseFloat(quantity) || 0,
            rate: parseFloat(rate) || 0,
            amount: parseFloat(amount) || 0,
            remarks: remarks
        };
        
        saleItems.push(item);
        updateSaleItemsTable();
        
        // Clear form
        $('#saleQuantity, #saleRate, #saleAmount, #saleRemarks').val('');
    });
    
    // Calculate sale amount automatically
    $('#saleQuantity, #saleRate').on('input', function() {
        const quantity = parseFloat($('#saleQuantity').val()) || 0;
        const rate = parseFloat($('#saleRate').val()) || 0;
        const amount = quantity * rate;
        $('#saleAmount').val(amount.toFixed(2));
    });
    
    // Production form submission
    $('#productionForm').on('submit', function(e) {
        e.preventDefault();
        
        if (productionItems.length === 0) {
            alert('Please add at least one production item');
            return;
        }
        
        const operatorId = $('#prodOperator').val();
        if (!operatorId) {
            alert('Please select an operator');
            return;
        }
        
        const data = {
            number: $('#prodNumber').val(),
            date: $('#prodDate').val(),
            shift: $('#prodShift').val(),
            operator_id: parseInt(operatorId),
            items: productionItems
        };
        
        $.ajax({
            url: '/api/save_production',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                if (response.success) {
                    alert(response.message);
                    $('#productionForm')[0].reset();
                    productionItems = [];
                    updateProductionItemsTable();
                    // Update production number
                    const nextNum = incrementNumber($('#prodNumber').val());
                    $('#prodNumber').val(nextNum);
                } else {
                    alert(response.message);
                }
            },
            error: function() {
                alert('Error saving production');
            }
        });
    });
    
    // Sale form submission
    $('#saleForm').on('submit', function(e) {
        e.preventDefault();
        
        if (saleItems.length === 0) {
            alert('Please add at least one sale item');
            return;
        }
        
        const partyId = $('#saleParty').val();
        if (!partyId) {
            alert('Please select a party');
            return;
        }
        
        const data = {
            order_no: $('#saleOrderNo').val(),
            date: $('#saleDate').val(),
            party_id: parseInt(partyId),
            items: saleItems
        };
        
        $.ajax({
            url: '/api/save_sale',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                if (response.success) {
                    alert(response.message);
                    $('#saleForm')[0].reset();
                    saleItems = [];
                    updateSaleItemsTable();
                    // Update sale number
                    const nextNum = incrementNumber($('#saleOrderNo').val());
                    $('#saleOrderNo').val(nextNum);
                } else {
                    alert(response.message);
                }
            },
            error: function() {
                alert('Error saving sale');
            }
        });
    });
}

function updateProductionItemsTable() {
    const tbody = $('#productionItemsBody');
    tbody.empty();
    
    productionItems.forEach((item, index) => {
        const row = `
            <tr>
                <td>${item.item_name}</td>
                <td>${item.machine_name}</td>
                <td>${item.length}</td>
                <td>${item.weight}</td>
                <td>${item.remarks}</td>
                <td>
                    <button class="btn btn-sm btn-danger remove-prod-item" data-index="${index}">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
        tbody.append(row);
    });
}

function updateSaleItemsTable() {
    const tbody = $('#saleItemsBody');
    tbody.empty();
    
    saleItems.forEach((item, index) => {
        const row = `
            <tr>
                <td>${item.item_name}</td>
                <td>${item.quantity}</td>
                <td>${item.rate}</td>
                <td>${item.amount}</td>
                <td>${item.remarks}</td>
                <td>
                    <button class="btn btn-sm btn-danger remove-sale-item" data-index="${index}">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
        tbody.append(row);
    });
}

// Remove production item
$(document).on('click', '.remove-prod-item', function() {
    const index = $(this).data('index');
    productionItems.splice(index, 1);
    updateProductionItemsTable();
});

// Remove sale item
$(document).on('click', '.remove-sale-item', function() {
    const index = $(this).data('index');
    saleItems.splice(index, 1);
    updateSaleItemsTable();
});

function incrementNumber(current) {
    if (current.startsWith('DP')) {
        const num = parseInt(current.slice(2)) + 1;
        return `DP${num.toString().padStart(3, '0')}`;
    } else if (current.startsWith('JOB')) {
        const num = parseInt(current.slice(3)) + 1;
        return `JOB${num.toString().padStart(3, '0')}`;
    }
    return current;
}

// Help and user management
function initHelp() {
    // User management (admin only)
    $('#userForm').on('submit', function(e) {
        e.preventDefault();
        
        const username = $('#newUsername').val();
        const password = $('#newPassword').val();
        const role = $('#newRole').val();
        
        if (!username || !password) {
            alert('Username and password are required');
            return;
        }
        
        $.ajax({
            url: '/api/add_user',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ username, password, role }),
            success: function(response) {
                if (response.success) {
                    alert(response.message);
                    $('#userForm')[0].reset();
                    location.reload();
                } else {
                    alert(response.message);
                }
            },
            error: function() {
                alert('Error adding user');
            }
        });
    });
    
    // Delete user
    $(document).on('click', '.delete-user', function() {
        const userId = $(this).data('id');
        const username = $(this).closest('tr').find('td:nth-child(2)').text();
        
        if (confirm(`Are you sure you want to delete user "${username}"?`)) {
            $.ajax({
                url: '/api/delete_user',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ id: userId }),
                success: function(response) {
                    if (response.success) {
                        alert(response.message);
                        location.reload();
                    }
                },
                error: function() {
                    alert('Error deleting user');
                }
            });
        }
    });
}