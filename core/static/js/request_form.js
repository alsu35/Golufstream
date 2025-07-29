// Добавляет на страницу новую строку перерыва с заданным временем начала и конца.
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

// Добавить новую строку
document.getElementById('add-break-btn')
    .addEventListener('click', () => addBreakPeriod());

// Удаление строки
document.getElementById('break-periods-container').addEventListener('click', function (e) {
    if (e.target.classList.contains('remove-break-btn')) {
        e.target.closest('.break-row').remove();
    }
});

// При сабмите сериализуем
document.querySelector('form').addEventListener('submit', function () {
    const out = [];
    document.querySelectorAll('#break-periods-container .break-row').forEach(row => {
        const s = row.querySelector('.break-start').value;
        const e = row.querySelector('.break-end').value;
        if (s && e) out.push(`${s}-${e}`);
    });
    document.getElementById('id_break_periods').value = JSON.stringify(out);
});

// Считывает из скрытого <input id="id_break_periods"> JSON-массив перерывов и инициализирует их на форме.
function initDatepickers() {
    // flatpickr для дат
    const datePickerConfig = {
        locale: "ru",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d.m.Y",
        allowInput: true,
        onChange: function (selectedDates, dateStr, instance) {
            instance.input.classList.toggle('is-invalid', selectedDates.length === 0);
        }
    };

    flatpickr("#id_date_start", datePickerConfig);
    flatpickr("#id_date_end", datePickerConfig);


    // flatpickr для времени
    flatpickr("#{{ form.time_start.id_for_label }}", {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
        time_24hr: true,
    });

    flatpickr("#{{ form.time_end.id_for_label }}", {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
        time_24hr: true,
    });
}
        
// Настраивает отображение для поля «ответственный» с кастомным шаблоном
function formatPersonal(option) {
    if (!option.id) {
    return option.text; 
    }
    const fullName    = option.text;
    const department = $(option.element).data('department') || '';
    return $(`
    <div>
        <div><strong>${department}</strong></div>
        <small class="text-muted">${fullName}</small>
    </div>
    `);
}

// 2) Инициализация Select2 на нашем селекте
$('.change-responsible').select2({
    theme: 'bootstrap-5',
    placeholder: 'Выберите ответственного',
    allowClear: false,
    width: 'resolve',
    templateResult: formatPersonal,
    templateSelection: formatPersonal,
    escapeMarkup: m => m
});

// Select2 для заказчика
$('.change-customer').select2({
    theme: 'bootstrap-5',
    placeholder: 'Выберите заказчика',
    width: 'resolve',
    templateResult: formatPersonal,
    templateSelection: formatPersonal,
    escapeMarkup: m => m
});

// 3) AJAX‑обновление ответственного при выборе
$('.change-responsible').on('change', function() {
    const $sel          = $(this),
        requestId    = $sel.data('id'),
        responsibleId= $sel.val();

    // если создаём новую заявку (нет ID) — просто вернёмся
    if (!requestId) return;

    fetch("{% url 'update_responsible' %}", {
    method: "POST",
    headers: {
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        request_id:     requestId,
        responsible_id: responsibleId
    })
    })
    .then(r => r.json())
    .then(js => {
    if (!js.success) {
        alert('Ошибка: ' + js.error);
    }
    });
});

document.addEventListener("DOMContentLoaded", function () {
    // Глобальные ссылки на элементы времени
    const startInput = document.getElementById("id_time_start");
    const endInput = document.getElementById("id_time_end");
    const output = document.getElementById("timeDifference"); 

    const LIFTING_CODE = 'lifting';
    const categorySelect = document.getElementById('id_equipment_category');
    const liftingBlock = document.getElementById('liftingFields');

    function toggleLiftingFields() {
        if (!categorySelect || !liftingBlock) return;
        
        const selectedOption = categorySelect.options[categorySelect.selectedIndex];
        const code = selectedOption.dataset.code;
        
        if (code === LIFTING_CODE) {
            liftingBlock.style.display = 'block';
        } else {
            liftingBlock.style.display = 'none';
        }
    }

    if (categorySelect) {
        categorySelect.addEventListener('change', toggleLiftingFields);
        toggleLiftingFields(); // Инициализация при загрузке
    }

    function calculateTimeDifference() {
        if (!startInput || !endInput || !output) return;

        const start = startInput.value;
        const end = endInput.value;

        if (!start || !end) {
            output.textContent = "⏱ Продолжительность времени (автоматически): —";
            return;
        }

        const [startH, startM] = start.split(":").map(Number);
        const [endH, endM] = end.split(":").map(Number);

        const startMinutes = startH * 60 + startM;
        const endMinutes = endH * 60 + endM;

        const diff = endMinutes - startMinutes;

        if (diff <= 0) {
            output.textContent = "⏱ Время окончания должно быть позже начала";
            return;
        }

        const hours = Math.floor(diff / 60);
        const minutes = diff % 60;

        output.textContent = `⏱ Продолжительность времени (автоматически): ${hours} ч ${minutes} мин`;
    }

    // События времени
    if (startInput && endInput) {
        startInput.addEventListener("change", calculateTimeDifference);
        endInput.addEventListener("change", calculateTimeDifference);
        calculateTimeDifference();
    }

    let existing = [];
    try {
        const raw = document.getElementById('id_break_periods').value;
        if (raw) existing = JSON.parse(raw); // ["03:30-03:04", "16:30-16:00"]
    } catch (e) {}

    existing.forEach(str => {
        if (typeof str === "string" && str.includes("-")) {
            const [start, end] = str.split("-");
            addBreakPeriod(start, end);
        }
    });
    initDatepickers();
});