document.addEventListener("DOMContentLoaded", function () {
    console.log("Fresh Basket grocery website loaded.");

    const mobileInputs = document.querySelectorAll(
        'input[name="mobile"]'
    );

    mobileInputs.forEach(function (input) {
        input.addEventListener("input", function () {
            this.value = this.value.replace(/\D/g, "").slice(0, 10);
        });
    });

    const pincodeInputs = document.querySelectorAll(
        'input[name="pincode"]'
    );

    pincodeInputs.forEach(function (input) {
        input.addEventListener("input", function () {
            this.value = this.value.replace(/\D/g, "").slice(0, 6);
        });
    });
});
