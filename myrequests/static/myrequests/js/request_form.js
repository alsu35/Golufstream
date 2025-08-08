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
document.querySelector('form').addEventListener('submit', function (e) {
    console.log("📝 Сабмит формы заявки");
    const out = [];
    document.querySelectorAll('#break-periods-container .break-row').forEach(row => {
        const s = row.querySelector('.break-start').value;
        const e = row.querySelector('.break-end').value;
        if (s && e) out.push(`${s}-${e}`);
    });

    console.log("🕒 Перерывы сериализованы:", out);
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
    .then(r => {
        console.log("📥 Ответ от update_responsible:", r.status);
        return r.json();
    })
    .then(js => {
        console.log("📥 JSON-ответ:", js);
        if (!js.success) {
            alert('Ошибка: ' + js.error);
        }
    })
    .catch(err => {
        console.error("❌ Ошибка при fetch:", err);
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

    const modalEl = document.getElementById('addProfileModal');
    if (!modalEl) {
        // На этой странице нет модалки — выходим и ничего не делаем
        return;
    }
    const errorsBox = modalEl.querySelector('.all-errors-container');
    const form = document.getElementById('addProfileForm');
    const respSelect = $('#id_responsible');
    const addUrl = modalEl.dataset.addResponsibleUrl;

    const phoneField = document.getElementById('profilePhone');

    if (!modalEl) {
        // На этой странице нет модалки — выходим и ничего не делаем
        return;
    }

    // Маска телефона +7-999-999-99-99
    if (phoneField) {
        $('#profilePhone').inputmask({
            mask: '+7-999-999-99-99',
            placeholder: '_',
            showMaskOnHover: false,
            autoUnmask: false,
            clearIncomplete: true
        });
    }

    // Select2 для department в модалке
    $('#profileDepartment').select2({
        placeholder: 'Выберите подразделение',
        dropdownParent: modalEl,
        width: '100%',
        theme: 'default',
        templateResult: formatOption, 
        templateSelection: formatOption 
    });

    $('#profileLocation').select2({
        placeholder: 'Выберите локацию',
        dropdownParent: $('#addProfileModal'),
        width: '100%',
        theme: 'default'
    });

    function formatOption(option) {
        if (!option.id) return option.text;
        return $(`<span style="color: white;">${option.text}</span>`);
    }

    if (form){
            form.addEventListener('submit', e => {
                e.preventDefault();
                errorsBox.innerHTML = '';

                const data = {
                    last_name: form.elements['last_name'].value.trim(),
                    first_name: form.elements['first_name'].value.trim(),
                    middle_name: form.elements['middle_name'].value.trim(),
                    position: form.elements['position'].value.trim(),
                    phone: $('#profilePhone').val(),
                    birth_date: form.elements['birth_date'].value,
                    department: form.elements['department'].value,
                    location: form.elements['location'].value,
                    csrfmiddlewaretoken: form.querySelector('[name=csrfmiddlewaretoken]').value
                };


            // Клиентская валидация
            const required = [
                { val: data.last_name,  name: 'Фамилия' },
                { val: data.first_name, name: 'Имя' },
                { val: data.position,   name: 'Должность' },
                { val: data.phone,      name: 'Телефон' },
                { val: data.department, name: 'Подразделение' },
                { val: data.location,   name: 'Локация' }
            ];
            // console.log("Отправка AJAX-запроса на сохранение ответственного", data);
            let ok = true;
            required.forEach(f => {
                if (!f.val) {
                    ok = false;
                    errorsBox.insertAdjacentHTML('beforeend',
                        `<div class="all-error-message">Поле «${f.name}» обязательно</div>`);
                }
            });
            if (!ok) return;

            // AJAX POST
            $.post(addUrl, data)
            .done(res => {
                // Добавляем в Select2
                const opt = new Option(res.full_name, res.profile_id, true, true);
                $(opt).attr('data-department', res.department_display);
                respSelect.append(opt).trigger('change');
                // Сбрасываем форму и закрываем
                form.reset();
                $('#profileDepartment,#profileLocation').val(null).trigger('change');
                bootstrap.Modal.getInstance(modalEl).hide();
            })
            .fail(xhr => {
                try {
                    console.error("❌ Ошибка при отправке формы ответственного:", xhr);
                    const response = JSON.parse(xhr.responseText);
                    if (response.errors) {
                        // Очищаем предыдущие ошибки
                        errorsBox.innerHTML = '';
                        $('.is-invalid').removeClass('is-invalid');
                        
                        // Добавляем ошибки под соответствующие поля
                        Object.keys(response.errors).forEach(field => {
                            const errors = response.errors[field];
                            const inputField = $(`#profile${field.charAt(0).toUpperCase() + field.slice(1)}`);
                            let errorContainer;
                            
                            // Проверяем, есть ли специальный контейнер для ошибок
                            const inputGroup = inputField.closest('.input-group');
                            errorContainer = inputGroup.find('.invalid-feedback');
                            
                            if (errorContainer.length) {
                                // Если контейнер для ошибок найден
                                errorContainer.html(errors.join('<br>')).show();
                                inputField.addClass('is-invalid');
                            } else {
                                // Или добавляем в общий контейнер ошибок
                                errors.forEach(error => {
                                    const errorBox = document.createElement('div');
                                    errorBox.className = 'all-error-message';
                                    errorBox.innerHTML = `<strong>${inputGroup.find('label').text().replace('*', '')}:</strong> ${error}`;
                                    errorsBox.appendChild(errorBox);
                                });
                            }
                        });
                    }
                } catch (e) {
                    errorsBox.innerHTML = `<div class="all-error-message">Ошибка при сохранении данных</div>`;
                }
            });
        });

    }else{
        console.error("Форма addProfileForm не найдена!");
        return;
    }

    // Очистка при закрытии
    modalEl.addEventListener('hidden.bs.modal', () => {
        errorsBox.innerHTML = '';
        form.reset();                     // теперь работает
        $('#profileDepartment,#profileLocation').val(null).trigger('change');
    });


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
