    $(function(){
    // ========================
    // Добавляет на страницу новую строку перерыва с заданным временем начала и конца.
    // ========================
    function addBreakPeriod(start = "", end = "") {
        const container = document.getElementById("break-periods-container");

        const row = document.createElement("div");
        row.className = "d-flex align-items-center gap-2 mb-2 break-row";

        row.innerHTML = `
            <input type="time" class="form-control break-start" value="${start}">
            <span>до</span>
            <input type="time" class="form-control break-end" value="${end}">
            <button type="button" class="btn btn-sm btn-outline-danger remove-break-btn">&times;</button>
        `;

        container.appendChild(row);
    }

    // ========================
    // Переменные
    // ========================
    const $statusFilter     = $('#statusFilter');
    const $locationFilter   = $('#locationFilter');
    const $categoryFilter   = $('#categoryFilter');
    const $requestsTableBody= $('#requestsTable tbody');
    let sortDirection       = "desc";
    let dateStartPicker, dateEndPicker;

    // Массив столбцов по умолчанию для экспорта
    const defaultColumns = [
        'ID',
        'Дата подачи',
        'Время подачи',
        'Подразделение',
        'Ответственный',
        'Заказчик',
        'Дата начала работы',
        'Дата окончания работы',
        'Время начала работ',
        'Время окончания работ',
        'Окончание работ по факту',
        'Перерывы',
        'Объем работы (чч:мм)',
        'Локация',
        'Категория',
        'Вид транспорта',
        'Вид работ',
        'Объект работ',
        'Статус',
        'Комментарий',
        'Номер удостоверения ответственного',
        'ФИО стропольщика',
        'Номера удостоверений стропольщиков'
    ];

    // ========================
    // Инициализация flatpickr
    // ========================
    function initDatePickers(){
        const cfg = {
            locale: "ru",
            dateFormat: "Y-m-d",
            altFormat:  "d.m.Y",
            altInput:   true,
            allowInput: true,
            onChange:   filterRequests
        };
        dateStartPicker = flatpickr("#dateStartFilter", cfg);
        dateEndPicker   = flatpickr("#dateEndFilter",   cfg);
    }

    // ========================
    // Сортировка по дате
    // ========================
    function initSorting(){
        $("#sortDateHeader").on("click", function(){
            const rows = $requestsTableBody.find("tr").get();
            sortDirection = sortDirection === "asc" ? "desc" : "asc";
            $(this).removeClass("asc desc").addClass(sortDirection);
            rows.sort((a,b)=>{
                const da = new Date(a.getAttribute("created-at"));
                const db = new Date(b.getAttribute("created-at"));
                return sortDirection==="asc" ? da-db : db-da;
            });
            $requestsTableBody.append(rows);
        });
    }

    // ========================
    // Сбор и запись условий поиска
    // ========================
    function updateSearchConditions(){
        const terms = $('.search-input')
            .map((_,el)=>el.value.trim())
            .get()
            .filter(Boolean);
        $('#searchConditions').val(JSON.stringify(terms));
    }

    // ========================
    // Фильтрация всех строк
    // ========================
    function filterRequests(){
        const searchTerms = $('.search-input').map(function(){
            return $(this).val().trim().toLowerCase();
        }).get().filter(Boolean);

        const filters = {
            status:    $statusFilter.val(),
            location:  $locationFilter.val(),
            category:  $categoryFilter.val(),
            dateStart: $("#dateStartFilter").val(),
            dateEnd:   $("#dateEndFilter").val()
        };

        $requestsTableBody.find("tr").each(function(){
            const $row = $(this);
            const data = {
                id:           String($row.data("id")),
                status:       $row.data("status"),
                location:     $row.data("location"),
                category:     $row.data("equipment-category"),
                customer:     $row.data("customer")   || "",
                responsible:  $row.data("responsible")|| "",
                workType:     $row.data("work-type")  || "",
                workObject:   $row.data("work-object")|| "",
                transportType:$row.data("transport-type")||"",
                department:   $row.data("department") || "",
                dateStart:    $row.data("date-start"),
                dateEnd:      $row.data("date-end"),
                timeStart:    $row.data("time-start") || "",
                timeEnd:      $row.data("time-end") || "",
                isCompletedFact: $row.data("is-completed-fact") === "yes",
                breakPeriods: $row.data("break-periods") || [],
                comment:      $row.data("comment") || "",
                responsibleCertificate: $row.data("responsible-id-card") || "",
                slingers:     $row.data("slingers") || { names: "", certificates: "" }
            };

            // Текстовый поиск
            const matchesSearch = searchTerms.every(term=>
                data.id.includes(term) ||
                data.workType.toLowerCase().includes(term) ||
                data.workObject.toLowerCase().includes(term) ||
                data.transportType.toLowerCase().includes(term) ||
                data.customer.toLowerCase().includes(term) ||
                data.responsible.toLowerCase().includes(term) ||
                data.department.toLowerCase().includes(term)
            );

            // Селекты и даты
            const matches = {
                status:   !filters.status   || data.status   === filters.status,
                location: !filters.location || data.location === filters.location,
                category: !filters.category || data.category === filters.category,
                date:     (!filters.dateStart && !filters.dateEnd) ||
                        (
                            data.dateStart && data.dateEnd &&
                            (!filters.dateStart || data.dateStart >= filters.dateStart) &&
                            (!filters.dateEnd   || data.dateEnd   <= filters.dateEnd)
                        )
            };

            // Итоговый результат
            const isVisible = matchesSearch && matches.status && matches.location && matches.category && matches.date;
            $row.toggle(isVisible);
        });
        
        updateUrlParams();
    }

    // ========================
    // Обновление URL-параметров
    // ========================
    function updateUrlParams(){
        const p = new URLSearchParams();
        const vals = {
            status:   $statusFilter.val(),
            location: $locationFilter.val(),
            category: $categoryFilter.val(),
            date_start: $("#dateStartFilter").val(),
            date_end:   $("#dateEndFilter").val()
        };
        Object.entries(vals).forEach(([k,v])=>v && p.set(k,v));
        history.replaceState(null,'',window.location.pathname+'?'+p.toString());
    }

    // ========================
    // Динамический поиск: +, x, авто‑фильтрация
    // ========================
    // 1) превращаем главный input в search-input
    $('#searchInput').addClass('search-input');

    // 2) добавление по "+"
    $('#add-search-btn').on('click',function(){
        const v = $('#searchInput').val().trim();
        if(!v) return;
        const $row = $(`
            <div class="input-group mb-1 search-row">
                <input type="text" class="form-control search-input" value="${v}" placeholder="Поиск по заявкам...">
                <button type="button" class="btn btn-danger btn-sm remove-search-btn"><i class="bi bi-x"></button>
            </div>
        `);
        $('#add-search-container').append($row);
        $('#searchInput').val('');
        updateSearchConditions();
        filterRequests();
    });

    // 3) удаление строки
    $(document).on('click','.remove-search-btn',function(){
        $(this).closest('.search-row').remove();
        updateSearchConditions();
        filterRequests();
    });

    // 4) авто‑фильтрация при вводе
    $(document).on('input','.search-input',function(){
        updateSearchConditions();
        filterRequests();
    });

    // ========================
    // Очистка всех фильтров
    // ========================
    function clearAllFilters(){
        // поиск
        $('#add-search-container').empty();
        $('#searchInput').val('');
        $('#searchConditions').val('');
        // селекты
        $statusFilter.val('').trigger('change');
        $locationFilter.val('').trigger('change');
        $categoryFilter.val('').trigger('change');
        // даты и сортировка
        dateStartPicker.clear();
        dateEndPicker.clear();
        $('#sortDateHeader').removeClass('asc desc');
        sortDirection = 'desc';
        filterRequests();
    }

    $('#clearAllFilter').attr('type','button').off('click').on('click', e=>{
        localStorage.removeItem('savedFilters');
        e.preventDefault();
        clearAllFilters();
    });

    // ========================
    // инциализация и цвета статусов
    // ========================
    function applyStatusColor($el) {
        $el.removeClass('status-new status-assigned status-work status-done status-cancel');
        const code = $el.data('code') || $el.find('option:selected').data('code');
        if (code) $el.addClass(`status-${code}`);
    }

    function initStatuses() {
        $('.change-status, .status-badge.change-status').each(function () {
            applyStatusColor($(this));
        });
        $('.change-status').filter('select').on('change', function () {
            const $sel = $(this);
            const id = $sel.data("id");
            const stId = $sel.val();
            const stCode = $sel.find('option:selected').data('code');
            $sel.data('code', stCode);
            applyStatusColor($sel);
            // в request_list переменная UPDATE_STATUS_URL
            fetch(window.UPDATE_STATUS_URL, {
                method: "POST",
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ request_id: id, status_id: stId })
            })
            .then(r => r.json())
            .then(js => { 
                if (!js.success){
                    alert('Ошибка: ' + js.error);
                }  else{
                    location.reload();
                }
            });
        });
    }

    // ========================
    // Инициализация селектов ответственных
    // ========================
    function initResponsibleSelects() {
        function formatResponsible(option) {
            if (!option.id) return option.text;
            const position = $(option.element).data('position') || '';
            const name = option.text;
            return $(`
                <div class="d-flex flex-column p-0 m-0">
                    <div><strong>${name}</strong></div>
                    <small class="text-muted">${position}</small>
                </div>
            `);
        }
        $('.change-responsible').select2({
            theme: 'bootstrap-5',
            placeholder: 'Выберите ответственного',
            allowClear: false,
            width: 'resolve',
            templateResult: formatResponsible,
            templateSelection: formatResponsible,
            escapeMarkup: m => m
        }).on("change", function () {
            const $sel = $(this);
            const requestId = $sel.data("id");
            const responsibleId = $sel.val();
            // в request_list переменная UPDATE_RESPONSIBLE_URL
            fetch(window.UPDATE_RESPONSIBLE_URL, {
                method: "POST",
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ request_id: requestId, responsible_id: responsibleId })
            })
            .then(r => r.json())
            .then(js => { 
                if (!js.success) alert('Ошибка: ' + js.error); 
            });
        });
    }

    // ========================
    // Сохранение фильтров
    // ========================
    function saveCurrentFilters() {
        const filters = {
            status:   $statusFilter.val(),
            location: $locationFilter.val(),
            category: $categoryFilter.val(),
            dateStart: $("#dateStartFilter").val(),
            dateEnd:   $("#dateEndFilter").val(),
            searchTerms: $('.search-input')
                .map((_, el) => $(el).val().trim())
                .get()
                .filter(Boolean)
        };
        try {
            localStorage.setItem('savedFilters', JSON.stringify(filters));
            alert('Фильтры успешно сохранены!');
        } catch (e) {
            console.error('Ошибка сохранения в localStorage', e);
            alert('Не удалось сохранить фильтры (localStorage переполнен или недоступен)');
        }
    }

    // Привязка к кнопке
    $('#saveFiltersBtn').on('click', function () {
        saveCurrentFilters();
    });

    // ========================
    // Загрузка сохранённых фильтров
    // ========================
    function loadSavedFilters() {
        const saved = localStorage.getItem('savedFilters');
        if (!saved) return;
        try {
            const filters = JSON.parse(saved);
            // Установка значений фильтров
            if (filters.status)     $statusFilter.val(filters.status);
            if (filters.location)   $locationFilter.val(filters.location);
            if (filters.category)   $categoryFilter.val(filters.category);
            if (filters.dateStart)  dateStartPicker.setDate(filters.dateStart);
            if (filters.dateEnd)    dateEndPicker.setDate(filters.dateEnd);
            // Очистка текущих поисковых строк
            $('#add-search-container').empty();
            // Восстановление поисковых строк
            filters.searchTerms.forEach(term => {
                const $row = $(`
                    <div class="input-group mb-1 search-row">
                        <input type="text" class="form-control search-input" value="${term}" placeholder="Поиск по заявкам...">
                        <button type="button" class="btn btn-danger btn-sm remove-search-btn"><i class="bi bi-x"></i></button>
                    </div>
                `);
                $('#add-search-container').append($row);
            });
            updateSearchConditions();
        } catch (e) {
            console.error('Ошибка при загрузке фильтров из localStorage', e);
        }
    }

    // ========================
    // Генерация Excel
    // ========================
    async function generateExcel(headers, data, rowStatuses) {
        const wb = new ExcelJS.Workbook();
        const ws = wb.addWorksheet('Заявки', { views: [{ state: 'frozen', ySplit: 1 }] });

        // Цвета статусов
        const statusFills = {
            new:      { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF4D867' } }, // Жёлтый
            assigned: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFD1B3FF' } }, // Лавандовый
            work:     { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFB2EAC3' } }, // Бирюзовый
            done:     { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF88C9ED' } }, // Голубой
            cancel:   { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFFF9696' } }, // Красный
        };
            
        // Добавляем заголовки
        ws.addRow(headers);

        // Добавляем данные
        data.forEach((rowValues, idx) => {
            const excelRow = ws.addRow(rowValues);

            // Применяем цвет строки по статусу
            const statusCode = rowStatuses[idx];
            const fillStyle = statusFills[statusCode];

            if (fillStyle) {
                excelRow.eachCell(cell => {
                    cell.fill = fillStyle;
                });
            }
        });

        // Стили
        ws.columns.forEach((col, i) => {
            col.eachCell((cell, rowNumber) => {
                cell.alignment = { vertical: 'middle', horizontal: 'center', wrapText: true };
                cell.border = {
                    top: { style: 'thin' }, left: { style: 'thin' },
                    bottom: { style: 'thin' }, right: { style: 'thin' }
                };
                if (rowNumber === 1) {
                    cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFDDDDDD' }};
                    cell.font = { bold: true };
                }
            });

            // Автоподгонка ширины
            let max = 10;
            col.eachCell(cell => {
                const v = cell.value ? cell.value.toString() : '';
                max = Math.max(max, v.length);
            });
            col.width = max + 2;
        });

        // Имя файла
        const today = new Date();
        const dd = String(today.getDate()).padStart(2, '0');
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        const yyyy = today.getFullYear();
        const filename = `Заявки ${dd}.${mm}.${yyyy}.xlsx`;

        // Сохранение
        const buf = await wb.xlsx.writeBuffer();
        saveAs(new Blob([buf], { type: 'application/octet-stream' }), filename);
    }
        
    // ========================
    // Инициализация модального окна выбора столбцов
    // ========================
    function initExportColumnModal() {
        const $modal = $('#exportColumnsModal');
        const checkboxes = $modal.find('.column-checkbox');

        // Загрузка сохранённых значений из localStorage
        function loadSavedColumns() {
            const saved = localStorage.getItem('exportColumns');
            if (saved) {
                const selected = JSON.parse(saved);
                checkboxes.each(function () {
                    const val = $(this).val();
                    $(this).prop('checked', selected.includes(val));
                });
            } else {
                checkboxes.prop('checked', false);
                checkboxes.each(function () {
                    const val = $(this).val();
                    $(this).prop('checked', defaultColumns.includes(val));
                });
            }
        }

        // Открытие модального окна
        $('#exportExcelBtn').on('click', function (e) {
            e.preventDefault();
            loadSavedColumns();
            $modal.modal('show');
        });

        // Сброс выбора
        $('#resetColumnsBtn').on('click', function () {
            checkboxes.prop('checked', false);
            checkboxes.each(function () {
                const val = $(this).val();
                $(this).prop('checked', defaultColumns.includes(val));
            });
        });

        // Сохранение выбора и экспорт
        $('#saveExportColumnsBtn').on('click', function () {
            const selected = checkboxes.filter(':checked').map(function () {
                return $(this).val();
            }).get();
            localStorage.setItem('exportColumns', JSON.stringify(selected));
            exportToExcel(selected);
        });
    }

    // ========================
    // формат для дат при экспорте
    // ========================
    function formatDate(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0'); // Месяцы с 0
        const year = date.getFullYear();
        return `${day}.${month}.${year}`;
    }
    
    // ========================
    // формат с заглавной 
    // ========================
    function capitalizeFirstLetter(str) {
        if (typeof str !== 'string' || !str.trim()) return str;
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }

    // ========================
    // формат с заглавной все слова
    // ========================
    function capitalizeWords(str) {
        if (typeof str !== 'string' || !str.trim()) return str;
        return str.toLowerCase().split(' ')
            .filter(Boolean)
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    // ========================
    // Функция экспорта в Excel
    // ========================
    function exportToExcel(selectedColumns) {
    const headers = selectedColumns;
    const data = [];
    const rowStatuses = [];

    $('#requestsTable tbody tr:visible').each(function () {
        const $tr = $(this);
        const row = [];
        const statusCode = $tr.data('status') || 'new';
        rowStatuses.push(statusCode);

        headers.forEach(header => {
        let value = '';

        switch (header) {
            case 'ID':
                value = $tr.data('id') || '';
                break;

            case 'Дата подачи':
                value = formatDate($tr.data('submitted')?.split('T')[0]);
                break;

            case 'Время подачи':
                value = $tr.data('submitted')?.split('T')[1]?.slice(0, 5) || '';
                break;

            case 'Подразделение':
                value = $tr.data('department') || '';
                break;

            case 'Ответственный':
                value = $tr.data('responsible') || '';
                break;

            case 'Заказчик':
                value = $tr.data('customer') || '';
                break;

            case 'Дата начала работы':
                value = formatDate($tr.data('date-start'));
                break;

            case 'Дата окончания работы':
                value = formatDate($tr.data('date-end'));
                break;

            case 'Время начала работ':
                value = $tr.data('time-start') || '';
                break;

            case 'Время окончания работ':
                value = $tr.data('time-end') || '';
                break;

            case 'Окончание работ по факту':
                value = $tr.data('is-completed-fact') ? 'Да' : 'Нет';
                break;

            case 'Перерывы': {
                const raw = $tr.attr('data-break-periods') || '[]';
                let breaksArr = [];
                try {
                    breaksArr = JSON.parse(raw);
                } catch (e) {
                    console.warn('Невалидный JSON в data-break-periods:', raw);
                }
                value = Array.isArray(breaksArr)
                    ? breaksArr.join(', ')
                    : '';
                break;
            }

            case 'Объем работы (чч:мм)': {
                const ts = $tr.data('time-start') || '';
                const te = $tr.data('time-end') || '';
                value = '';
                if (ts && te) {
                    // Разбираем время начала и окончания
                    const [h1, m1] = ts.split(':').map(Number);
                    const [h2, m2] = te.split(':').map(Number);

                    // Считаем общее количество минут
                    let diff = (h2 * 60 + m2) - (h1 * 60 + m1);
                    if (diff < 0) diff += 24 * 60; // переход через полночь

                    // Формируем строку "чч:мм"
                    const hours = Math.floor(diff / 60);
                    const minutes = diff % 60;
                    value = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
                }
                break;
            }
            case 'Локация':
                value = $tr.data('location-name') || '';
                break;

            case 'Категория':
                value = $tr.data('equipment-category-name') || '';
                break;

            case 'Вид транспорта':
                value = $tr.data('transport-type') || '';
                break;

            case 'Вид работ':
                value = $tr.data('work-type') || '';
                break;

            case 'Объект работ':
                value = $tr.data('work-object') || '';
                break;

            case 'Статус':
                value = $tr.data('status-name') || '';
                break;

            case 'Комментарий':
                value = $tr.data('comment') || '';
                break;

            case 'Номер удостоверения ответственного':
                value = $tr.data('responsible-id-card') || '';
                break;

            case 'ФИО стропольщика':
                value = $tr.data('slingers')?.names || '';
                break;

            case 'Номера удостоверений стропольщиков':
                value = $tr.data('slingers')?.certificates || '';
                break;

            default:
                value = '';
        }

        // Применяем форматирование текста
        if (typeof value === 'string' && value.trim()) {
            if (header === 'Ответственный' || header === 'Заказчик') {
            row.push(capitalizeWords(value));
            } else {
            row.push(capitalizeFirstLetter(value));
            }
        } else {
            row.push(value);
        }
        });

        data.push(row);
    });

    // Генерируем Excel
    generateExcel(headers, data, rowStatuses);
    }

    // ========================
    // Старт
    // ========================
    function init(){
        initDatePickers();
        initSorting();
        initStatuses();
        initResponsibleSelects();
        loadSavedFilters(); // Загрузка сохранённых фильтров
        
        // Привязка change-событий на селекты
        $statusFilter.on('change', filterRequests);
        $locationFilter.on('change', filterRequests);
        $categoryFilter.on('change', filterRequests);
        
        // Инициализация модального окна
        initExportColumnModal();
        
        // Инициализация фильтрации
        filterRequests();
    }
    
    init();
});
