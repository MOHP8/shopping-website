$(document).ready(function() {
    $('#passwordToggle, #confirmPasswordToggle').click(function() {
        var passwordField = $(this).closest('.input-group').find('input');
        var passwordFieldType = passwordField.attr('type');
        if (passwordFieldType === 'password') {
            passwordField.attr('type', 'text');
            $(this).find('i').removeClass('far fa-eye').addClass('far fa-eye-slash');
        } else {
            passwordField.attr('type', 'password');
            $(this).find('i').removeClass('far fa-eye-slash').addClass('far fa-eye');
        }
    });
});
