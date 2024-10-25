$(document).ready(function () {
    var searchTimer;

    // Live search functionality
    $('#searchInput').on('input', function () {
        clearTimeout(searchTimer);
        var query = $(this).val();

        if (query.length > 1) {
            searchTimer = setTimeout(function () {
                $.ajax({
                    url: LIVE_SEARCH_URL,  // Make sure this matches your URL configuration
                    data: {
                        'q': query
                    },
                    dataType: 'json',
                    success: function (data) {
                        var results = '';
                        var productResults = '';
                        var categoryResults = '';

                        data.results.forEach(function (item) {
                            var itemHtml = '<div class="search-item">';
                            itemHtml += '<a href="' + item.url + '">';
                            if (item.image) {
                                itemHtml += '<img src="' + item.image + '" alt="' + item.name + '" style="width: 50px; height: 50px;">';
                            }
                            itemHtml += '<span>' + item.name + '</span>';
                            itemHtml += '</a>';
                            itemHtml += '</div>';

                            if (item.type === 'product') {
                                productResults += itemHtml;
                            } else if (item.type === 'category') {
                                categoryResults += itemHtml;
                            }
                        });

                        if (productResults) {
                            results += '<h6>Products:</h6>' + productResults;
                        }
                        if (categoryResults) {
                            results += '<h6>Categories:</h6>' + categoryResults;
                        }

                        $('#liveSearchResults').html(results);
                    },
                    error: function (jqXHR, textStatus, errorThrown) {
                        console.error("AJAX error: " + textStatus + ' : ' + errorThrown);
                    }
                });
            }, 300);
        } else {
            $('#liveSearchResults').html('');
        }
    });

    // Handle search form submission
    $('#searchForm').on('submit', function (e) {
        e.preventDefault();
        var query = $('#searchInput').val();
        window.location.href = $(this).attr('action') + '?q=' + encodeURIComponent(query);
    });

    // Load search results
    function loadResults(url) {
        var formData = $('#filter-form').serialize();
        var sortValue = $('#sort').val();
        if (sortValue) {
            formData += '&sort=' + sortValue;
        }
        $.ajax({
            url: url,
            data: formData,
            success: function (data) {
                $('#search-results').html(data.html);
                $('#search-query').text(data.query);
                history.pushState(null, '', url + '?' + formData);
            }
        });
    }

    // Handle filter form submission
    $('#filter-form').on('submit', function (e) {
        e.preventDefault();
        loadResults($(this).attr('action'));
    });

    // Handle filter form changes
    $(document).on('change', '#filter-form select, #filter-form input', function () {
        loadResults($('#filter-form').attr('action'));
    });

    // Handle sort changes
    $('#sort').on('change', function () {
        loadResults($('#filter-form').attr('action'));
    });

    // Initial load for search results page
    if (window.location.pathname === '/search_results/') {  // Update this to match your actual URL
        loadResults(window.location.href);
    }
});

// User avatar popover
document.addEventListener('DOMContentLoaded', function () {
    var popoverTriggerEl = document.getElementById('userAvatar');
    if (popoverTriggerEl) {
        var popoverContent = document.getElementById('popoverContent').innerHTML;

        var popover = new bootstrap.Popover(popoverTriggerEl, {
            placement: 'bottom',
            trigger: 'manual',
            html: true,
            content: popoverContent
        });

        popoverTriggerEl.addEventListener('click', function (e) {
            e.preventDefault();
            popover.toggle();
        });

        document.addEventListener('click', function (e) {
            if (!popoverTriggerEl.contains(e.target) && !document.querySelector('.popover')?.contains(e.target)) {
                popover.hide();
            }
        });
    }
});
document.addEventListener('DOMContentLoaded', function() {
    const pills = document.querySelectorAll('.category-scroll .nav-item a');
    pills.forEach(pill => {
        pill.addEventListener('shown.bs.tab', function (e) {
            e.target.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'center'
            });
        });
    });
});