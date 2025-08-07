;(function () {
	// Инициализация маски для телефона
	function initPhoneMask() {
		$('#id_phone').inputmask({
			mask: '+7-999-999-99-99',
			placeholder: '_',
			showMaskOnHover: false,
			autoUnmask: false,
			clearIncomplete: true,
		})
	}

	// Проверка силы пароля и совпадения
	function validatePasswordStrength(password) {
		const errors = []
		if (password.length < 8)
			errors.push('Пароль должен содержать минимум 8 символов')
		if (!/[A-Z]/.test(password))
			errors.push('Пароль должен содержать хотя бы одну заглавную букву')
		if (!/[a-z]/.test(password))
			errors.push('Пароль должен содержать хотя бы одну строчную букву')
		if (!/[0-9]/.test(password))
			errors.push('Пароль должен содержать хотя бы одну цифру')
		return errors
	}

	// Проверка всех обязательных полей
	function validateRequiredFields() {
		const requiredFields = [
			'id_last_name',
			'id_first_name',
			'id_phone',
			'id_email',
			'id_password1',
			'id_password2',
			'id_position',
			'id_department',
			'id_role',
			'id_location',
		]
		let isValid = true
		const allErrorsContainer = document.querySelector('.all-errors-container')

		// Очищаем предыдущие ошибки
		const oldErrors = allErrorsContainer.querySelectorAll('.all-error-message')
		oldErrors.forEach(err => err.remove())

		// Проверяем обязательные поля
		requiredFields.forEach(fieldId => {
			const field = document.getElementById(fieldId)
			if (!field || !field.value.trim()) {
				isValid = false
				const errorBox = document.createElement('div')
				errorBox.className = 'all-error-message'
				const label = field.labels
					? field.labels[0].textContent.replace('*', '')
					: fieldId
				errorBox.innerHTML = `Поле "${label}" обязательно для заполнения`
				allErrorsContainer.appendChild(errorBox)
			}
		})
		return isValid
	}

	// Проверка email
	function validateEmail() {
		const emailField = document.getElementById('id_email')
		const email = emailField.value.trim()
		const allErrorsContainer = document.querySelector('.all-errors-container')

		if (!email) return true // Пустой email будет проверен как обязательное поле

		// Проверка формата email
		const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
		if (!emailRegex.test(email)) {
			const errorBox = document.createElement('div')
			errorBox.className = 'all-error-message'
			errorBox.innerHTML = 'Неверный формат email'
			allErrorsContainer.appendChild(errorBox)
			return false
		}
		return true
	}

	// Проверка телефона
	function validatePhone() {
		const phoneField = document.getElementById('id_phone')
		const phone = phoneField.value.trim()
		const allErrorsContainer = document.querySelector('.all-errors-container')

		if (!phone) return true // Пустой телефон будет проверен как обязательное поле

		// Проверка формата телефона (российский номер)
		const phoneRegex = /^\+7-\d{3}-\d{3}-\d{2}-\d{2}$/
		if (!phoneRegex.test(phone)) {
			const errorBox = document.createElement('div')
			errorBox.className = 'all-error-message'
			errorBox.innerHTML =
				'Неверный формат телефона. Используйте формат +7-XXX-XXX-XX-XX'
			allErrorsContainer.appendChild(errorBox)
			return false
		}
		return true
	}

	// Проверка пароля
	function validatePassword() {
		const password1 = document.getElementById('id_password1')
		const password2 = document.getElementById('id_password2')
		const allErrorsContainer = document.querySelector('.all-errors-container')
		let isValid = true

		// Проверка сложности пароля
		const errors = validatePasswordStrength(password1.value)
		if (errors.length > 0) {
			errors.forEach(error => {
				const errorBox = document.createElement('div')
				errorBox.className = 'all-error-message'
				errorBox.innerHTML = error
				allErrorsContainer.appendChild(errorBox)
			})
			isValid = false
		}

		// Проверка совпадения паролей
		if (password1.value !== password2.value) {
			const errorBox = document.createElement('div')
			errorBox.className = 'all-error-message'
			errorBox.innerHTML = 'Пароли не совпадают'
			allErrorsContainer.appendChild(errorBox)
			isValid = false
		}
		return isValid
	}

	// Проверка всех полей перед отправкой
	function validateAllFields() {
		let isValid = true

		// Проверяем обязательные поля
		if (!validateRequiredFields()) isValid = false

		// Проверяем email
		if (!validateEmail()) isValid = false

		// Проверяем телефон
		if (!validatePhone()) isValid = false

		// Проверяем пароль
		if (!validatePassword()) isValid = false

		return isValid
	}

	// Инициализация Select2
	function initSelect2() {
		// Инициализируем все выпадающие списки с классом 'select2'
		$('select').each(function () {
			// Проверяем, не инициализирован ли уже этот элемент
			if (!$(this).data('select2')) {
				$(this).select2({
					placeholder: 'Выберите...',
					allowClear: true,
					width: '100%',
				})
			}
		})
	}

	// Инициализация Select2 для подразделения
	function initDepartmentSelect() {
		$('.department-select').each(function () {
			// Проверяем, не инициализирован ли уже этот элемент
			if (!$(this).data('select2')) {
				$(this).select2({
					placeholder: 'Выберите организацию / подразделение',
					allowClear: false, // КРИТИЧЕСКИ ВАЖНО: отключаем крестик очистки
					width: '100%',
					dropdownParent: $(this).closest('.input-group'),
					minimumResultsForSearch: 5,
					templateResult: formatDepartment,
					templateSelection: formatDepartment,
					escapeMarkup: function (m) {
						return m
					},
				})
			}
		})
	}

	// Форматирование опций для поиска по двум полям
	function formatDepartment(department) {
		if (!department.id) {
			return department.text
		}

		const organization = $(department.element).data('organization')
		const $department = $(`<span>${organization} / ${department.text}</span>`)

		return $department
	}

	// Функция отображения текста (и поиска) по организации и подразделению
	function formatDepartmentText(dept) {
		return dept.text // text уже содержит "Организация / Подразделение"
	}

	$('.change-department').select2({
		theme: 'bootstrap-5', // или 'default' — зависит от вашего стиля
		placeholder: 'Выберите подразделение',
		allowClear: true,
		width: '100%',
		templateResult: formatDepartmentText,
		templateSelection: formatDepartmentText,
		escapeMarkup: m => m,
		matcher: function (params, data) {
			if ($.trim(params.term) === '') return data

			const term = params.term.toLowerCase()
			const text = data.text.toLowerCase()

			if (text.includes(term)) return data
			return null
		},
	})

	// Точка входа
	$(document).ready(function () {
		initPhoneMask()

		const form = document.querySelector('form')
		form.addEventListener('submit', function (e) {
			if (!validateAllFields()) {
				e.preventDefault()
				return false
			}
			return true
		})
	})
})()
