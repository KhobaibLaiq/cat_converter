function showForm(formId, button) {
    // Hide all forms
    document.querySelectorAll('.contact').forEach(form => form.style.display = 'none');
    // Show the selected form
    document.querySelector(`.${formId}`).style.display = 'block';

    // Remove active class from all buttons
    document.querySelectorAll('.cat_form, .pivot_form').forEach(btn => btn.classList.remove('active'));

    // Add active class to the clicked button
    button.classList.add('active');
}

// Define the browseDrive function to fetch files from Google Drive
function browseDrive() {
    $.ajax({
        url: '/bookkeeping/list_files_and_folders/',
        type: 'GET',
        data: { folder_id: 'root'},
        success: function(data) {
            populateDropdowns(data.files, "fileDropdown1");
            populateDropdowns(data.files, "fileDropdown2");
        },
        error: function(error) {
            console.error('Error:', error);
        }
    });
}

// Function to populate dropdown with fetched files
function populateDropdowns(files, dropdownId) {
    var dropdown = document.getElementById(dropdownId);
    dropdown.innerHTML = "";
    files.forEach(function(file) {
        var option = document.createElement("option");
        option.text = file[1];
        option.value = file[0]; // Assuming file[0] contains the sheet ID
        dropdown.add(option);
    });
}

// Function to handle form submission
function submitForm(formId) {
    $(formId).submit(function(event) {
        event.preventDefault(); // Prevent the form from submitting normally
        var selectedSheetId = $(formId + ' select').val(); // Get the selected sheet ID
        $.ajax({
            url: $(this).attr('action'),
            type: $(this).attr('method'),
            data: $(this).serialize() + '&sheetid=' + selectedSheetId, // Include the selected sheet ID
            success: function(response) {
                // Handle success
            },
            error: function(xhr, errmsg, err) {
                // Handle error
            }
        });
    });
}

// Call the submitForm function for both forms
$(document).ready(function() {
    submitForm('#form1');
    submitForm('#form2');
});

// Call the browseDrive function when clicking the "Refresh Sheet List" button for both dropdowns
$(document).ready(function() {
    $('.refresh').click(function() {
        browseDrive();
    });
});

function fetchDataAndUpdate() {
    var searchData = document.getElementById('searchData').value;
    console.log("searchData:", searchData); // Add this line for debugging
    if (searchData) {
      // Call a function to check if searchData is available in the search library
      console.log("Searching for:", searchData);
      checkSearchLibrary(searchData);
    }
}

function checkSearchLibrary(searchData) {
    // Get the CSRF token from the cookie
    var csrftoken = getCookie('csrftoken');
    console.log("CSRF Token:", csrftoken);

    // Send an AJAX request to the server to check if searchData is in the search library
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/bookkeeping/check_search_library/", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("X-CSRFToken", csrftoken); // Include the CSRF token in the request header
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            console.log("Server response:", xhr.responseText); // Add this line for debugging
            if (xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                console.log("Response:", response);
                if (response.categoryData) {
                    // If searchData is found in the search library, update the newData input field
                    console.log("Category data found:", response.categoryData);
                    document.getElementById('newData').value = response.categoryData;
                } else {
                    // If searchData is not found, you can handle it accordingly
                    console.log("Category data not found");
                }
            } else {
                console.error("Error:", xhr.status);
            }
        }
    };
    var data = JSON.stringify({ "searchData": searchData });
    xhr.send(data);
}

  
  // Function to get the value of a cookie by name
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        // Check if the cookie name matches
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          // Extract and return the cookie value
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

