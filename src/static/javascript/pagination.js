document.addEventListener('DOMContentLoaded', () => {

    const proposicoesTableBody = document.getElementById('proposicoes-table-body');
    const proposicoesPaginationControls = document.getElementById('proposicoes-pagination-controls');
    const filterSelect = document.getElementById('tipoFilter');
    
    const leisTableBody = document.getElementById('leis-table-body');
    const leisPaginationControls = document.getElementById('leis-pagination-controls');

    const autorNome = proposicoesTableBody.dataset.autorNome;

    function createPageItem(page, text = page, isDisabled = false, isActive = false) {
        const li = document.createElement('li');
        li.className = `page-item ${isDisabled ? 'disabled' : ''} ${isActive ? 'active' : ''}`;
        if (text === '...') {
            li.innerHTML = `<span class="page-link">...</span>`;
        } else {
            li.innerHTML = `<a class="page-link" href="#" data-page="${page}">${text}</a>`;
        }
        return li;
    }

    function updatePagination(paginationControls, totalPages, currentPage) {
        paginationControls.innerHTML = '';
        if (totalPages <= 1) return;

        paginationControls.appendChild(createPageItem(currentPage - 1, 'Anterior', currentPage === 1));

        const pagesToShow = [];
        const pagesAround = 2;

        if (totalPages <= (pagesAround * 2) + 3) {
            for (let i = 1; i <= totalPages; i++) pagesToShow.push(i);
        } else {
            pagesToShow.push(1);
            if (currentPage > pagesAround + 2) pagesToShow.push('...');
            for (let i = Math.max(2, currentPage - pagesAround); i <= Math.min(totalPages - 1, currentPage + pagesAround); i++) {
                pagesToShow.push(i);
            }
            if (currentPage < totalPages - pagesAround - 1) pagesToShow.push('...');
            pagesToShow.push(totalPages);
        }
        
        new Set(pagesToShow).forEach(page => {
             paginationControls.appendChild(createPageItem(page, page, false, page === currentPage));
        });

        paginationControls.appendChild(createPageItem(currentPage + 1, 'Próxima', currentPage === totalPages));
    }

    // --- PROPOSITIONS LOGIC ---
    let currentProposicaoPage = 1;
    let currentFilter = 'todos';

    async function fetchProposicoes(page = 1, filterType = 'todos') {
        proposicoesTableBody.innerHTML = '<tr><td colspan="7" class="text-center">Carregando...</td></tr>';
        try {
            const response = await fetch(`/api/proposicoes/${autorNome}?page=${page}&tipo=${filterType}`);
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            updateProposicoesTable(data.proposicoes);
            updatePagination(proposicoesPaginationControls, data.total_pages, data.current_page);
        } catch (error) {
            proposicoesTableBody.innerHTML = '<tr><td colspan="7" class="text-center">Erro ao carregar os dados.</td></tr>';
        }
    }

    function updateProposicoesTable(proposicoes) {
        proposicoesTableBody.innerHTML = '';
        if (proposicoes.length === 0) {
            proposicoesTableBody.innerHTML = '<tr><td colspan="7" class="text-center">Nenhuma proposição encontrada.</td></tr>';
            return;
        }
        proposicoes.forEach(p => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${p.processo || ''}</td> <td>${p.ano || ''}</td> <td>${p.tipo || ''}</td>
                <td>${p.assunto || ''}</td> <td>${p.data || ''}</td> <td>${p.situacao || ''}</td>
                <td>${p.arquivo ? `<a href="${p.arquivo}" target="_blank">Ver</a>` : 'N/A'}</td>
            `;
            proposicoesTableBody.appendChild(row);
        });
    }

    proposicoesPaginationControls.addEventListener('click', (e) => {
        e.preventDefault();
        const target = e.target;
        if (target.tagName === 'A' && !target.parentElement.classList.contains('disabled')) {
            const page = parseInt(target.dataset.page);
            fetchProposicoes(page, currentFilter);
        }
    });

    filterSelect.addEventListener('change', (e) => {
        currentFilter = e.target.value;
        currentProposicaoPage = 1;
        fetchProposicoes(currentProposicaoPage, currentFilter);
    });

    // --- START OF NEW LAW PROJECTS LOGIC ---
    let currentLeiPage = 1;

    async function fetchLeis(page = 1) {
        leisTableBody.innerHTML = '<tr><td colspan="6" class="text-center">Carregando...</td></tr>';
        try {
            const response = await fetch(`/api/leis/${autorNome}?page=${page}`);
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            updateLeisTable(data.leis);
            updatePagination(leisPaginationControls, data.total_pages, data.current_page);
        } catch (error) {
            leisTableBody.innerHTML = '<tr><td colspan="6" class="text-center">Erro ao carregar os dados.</td></tr>';
        }
    }

    function updateLeisTable(leis) {
        leisTableBody.innerHTML = '';
        if (leis.length === 0) {
            leisTableBody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum projeto de lei encontrado.</td></tr>';
            return;
        }
        leis.forEach(l => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${l.numero || ''}</td> <td>${l.ano || ''}</td> <td>${l.tema || ''}</td>
                <td>${l.resumo || ''}</td> <td>${l.data || ''}</td> <td>${l.situacao || ''}</td>
            `;
            leisTableBody.appendChild(row);
        });
    }

    leisPaginationControls.addEventListener('click', (e) => {
        e.preventDefault();
        const target = e.target;
        if (target.tagName === 'A' && !target.parentElement.classList.contains('disabled')) {
            const page = parseInt(target.dataset.page);
            fetchLeis(page);
        }
    });
    // --- END OF NEW LAW PROJECTS LOGIC ---

    fetchProposicoes(currentProposicaoPage, currentFilter);
    fetchLeis(currentLeiPage);
});