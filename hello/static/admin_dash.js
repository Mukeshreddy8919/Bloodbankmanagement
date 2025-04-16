        // JavaScript to handle operation button selection
        const operationButtons = document.querySelectorAll('.operation-button');
        operationButtons.forEach(button => {
            button.addEventListener('click', () => {
                operationButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
            });
        });

        document.getElementById('updateStockButton').addEventListener('click', function() {
            const bloodType = document.getElementById('blood_type').value;
            const operation = document.querySelector('.operation-button.active').getAttribute('data-operation');
            const units = document.getElementById('units').value;

            fetch(`/update_stock/${bloodType}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `operation=${operation}&units=${units}`,
            })
            .then(response => {
                if (response.ok) {
                    location.reload();
                } else {
                    alert('Failed to update stock.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred.');
            });
        });
