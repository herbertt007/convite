// ============================================================
// MAIN.JS — Convite Online Interativo
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    const cover = document.getElementById('envelope-cover');
    const waxSeal = document.getElementById('wax-seal');
    const invContent = document.getElementById('invitation-content');
    const btnAbrirForm = document.getElementById('btn-abrir-form');
    const modalConfirmacao = document.getElementById('modal-confirmacao');
    const btnFecharModal = document.getElementById('btn-fechar-modal');
    const formConfirmacao = document.getElementById('form-confirmacao');
    const btnEnviar = document.getElementById('btn-enviar');
    const btnText = document.getElementById('btn-text');
    const btnLoading = document.getElementById('btn-loading');
    const formFeedback = document.getElementById('form-feedback');
    const modalSucesso = document.getElementById('modal-sucesso');
    const sucessoMsg = document.getElementById('sucesso-msg');

    // Contador de pessoas
    const numPessoas = document.getElementById('numero_pessoas');
    document.getElementById('btn-plus').addEventListener('click', () => {
        if (parseInt(numPessoas.value) < 10) numPessoas.value = parseInt(numPessoas.value) + 1;
    });
    document.getElementById('btn-minus').addEventListener('click', () => {
        if (parseInt(numPessoas.value) > 1) numPessoas.value = parseInt(numPessoas.value) - 1;
    });

    // ── ABRIR ENVELOPE ──────────────────────────────────────
    function abrirEnvelope() {
        // Efeito sonoro de "rasgando" via vibração (mobile)
        if (navigator.vibrate) navigator.vibrate([30, 20, 50]);

        cover.classList.add('opening');
        cover.addEventListener('animationend', () => {
            cover.style.display = 'none';
            invContent.classList.remove('hidden');
        }, { once: true });
    }

    // Clique no lacre ou no cover
    waxSeal.addEventListener('click', (e) => {
        e.stopPropagation();
        abrirEnvelope();
    });
    cover.addEventListener('click', abrirEnvelope);

    // ── ABRIR MODAL DE CONFIRMAÇÃO ───────────────────────────
    btnAbrirForm.addEventListener('click', () => {
        modalConfirmacao.classList.remove('hidden');
        document.getElementById('nome').focus();
    });

    // ── FECHAR MODAL ─────────────────────────────────────────
    function fecharModal() {
        modalConfirmacao.classList.add('hidden');
        formConfirmacao.reset();
        numPessoas.value = 1;
        hideFeedback();
    }

    btnFecharModal.addEventListener('click', fecharModal);
    modalConfirmacao.addEventListener('click', (e) => {
        if (e.target === modalConfirmacao) fecharModal();
    });

    // ── ENVIAR CONFIRMAÇÃO ───────────────────────────────────
    formConfirmacao.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideFeedback();

        const nome = document.getElementById('nome').value.trim();
        const telefone = document.getElementById('telefone').value.trim();
        const numero_pessoas = parseInt(numPessoas.value);
        const mensagem = document.getElementById('mensagem').value.trim();

        if (!nome) {
            showFeedback('Por favor, informe seu nome!', 'error');
            document.getElementById('nome').focus();
            return;
        }

        // Loading state
        btnEnviar.disabled = true;
        btnText.classList.add('hidden');
        btnLoading.classList.remove('hidden');

        try {
            const res = await fetch('/confirmar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nome, telefone, numero_pessoas, mensagem })
            });
            const data = await res.json();

            if (data.success) {
                fecharModal();
                sucessoMsg.textContent = `Obrigado, ${nome}! Sua presença foi confirmada.`;
                modalSucesso.classList.remove('hidden');
            } else {
                showFeedback(data.message || 'Erro ao confirmar. Tente novamente.', 'error');
            }
        } catch (err) {
            showFeedback('Erro de conexão. Verifique sua internet.', 'error');
        } finally {
            btnEnviar.disabled = false;
            btnText.classList.remove('hidden');
            btnLoading.classList.add('hidden');
        }
    });

    // ── FEEDBACK HELPERS ─────────────────────────────────────
    function showFeedback(msg, type) {
        formFeedback.textContent = msg;
        formFeedback.className = `form-feedback ${type}`;
    }
    function hideFeedback() {
        formFeedback.className = 'form-feedback hidden';
        formFeedback.textContent = '';
    }

    // ── TELEFONE (sem máscara agressiva — evita travar no celular) ──
    const campoTelefone = document.getElementById('telefone');

    function digitosTelefone(valor) {
        let d = String(valor || '').replace(/\D/g, '');
        // +55 11 90000-0000 → remove DDI só quando vier com código do país
        if (d.length >= 12 && d.startsWith('55')) d = d.slice(2);
        return d.slice(0, 11);
    }

    function formatarTelefone(valor) {
        const d = digitosTelefone(valor);
        if (d.length <= 2) return d;
        if (d.length <= 7) return `${d.slice(0, 2)} ${d.slice(2)}`;
        if (d.length === 11) return `${d.slice(0, 2)} ${d.slice(2, 7)}-${d.slice(7)}`;
        return `${d.slice(0, 2)} ${d.slice(2, 6)}-${d.slice(6)}`;
    }

    campoTelefone.addEventListener('input', function () {
        this.value = formatarTelefone(this.value);
    });

    campoTelefone.addEventListener('blur', function () {
        if (this.value.trim()) this.value = formatarTelefone(this.value);
    });
});
