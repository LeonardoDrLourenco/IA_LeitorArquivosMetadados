// Função para enviar o formulário de upload
document.getElementById('uploadForm').onsubmit = async (event) => {
    event.preventDefault();

    const formData = new FormData();
    formData.append('file', document.getElementById('fileInput').files[0]);

    try {
        // Faz a requisição POST para o endpoint /enviar
        const response = await fetch('http://127.0.0.1:5000/enviar', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            alert("Arquivo enviado com sucesso!");
            
            // Chama a função para classificar o arquivo enviado
            await classificarArquivo(formData);
            
            // Atualiza os metadados
            carregarMetadados(); 
        } else if (response.status === 409) {
            alert("O arquivo já foi enviado anteriormente.");
        } else {
            const errorMessage = await response.json();
            alert("Erro ao enviar o arquivo: " + errorMessage.erro);
        }
    } catch (error) {
        console.error("Erro ao enviar o arquivo:", error);
        alert("Erro ao enviar o arquivo.");
    }
};

// Evento para exibir o nome do arquivo selecionado
document.getElementById('fileInput').addEventListener('change', (event) => {
    const fileName = event.target.files[0]?.name || 'Nenhum arquivo selecionado';
    document.getElementById('file-name').textContent = `Arquivo selecionado: ${fileName}`;
});


// Função para classificar o conteúdo do arquivo usando a API do Gemini
async function classificarArquivo(formData) {
    try {
        // Faz a requisição POST para o endpoint /analise
        const response = await fetch('http://127.0.0.1:5000/analise', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            alert(`Categoria do arquivo: ${data.classificacao}`);
        } else {
            const errorMsg = await response.json();
            alert("Erro ao classificar o arquivo: " + errorMsg.erro);
        }
    } catch (error) {
        console.error("Erro ao classificar o arquivo:", error);
        alert("Erro ao classificar o arquivo.");
    }
}

// Função para obter e exibir os metadados
async function carregarMetadados() {
    try {
        const response = await fetch('http://127.0.0.1:5000/metadados');
        if (!response.ok) throw new Error("Erro ao obter metadados.");

        const metadados = await response.json();
        const metadadosContainer = document.getElementById('metadados');
        metadadosContainer.innerHTML = '';

        metadados.forEach(metadado => {
            const metadadoDiv = document.createElement('div');
            metadadoDiv.innerHTML = `
                <p><strong>Id:</strong> ${metadado[0]} | <strong>Data:</strong> ${metadado[1]} | 
                <strong>Nome do Arquivo:</strong> ${metadado[2]} | <strong>Formato:</strong> ${metadado[3]} | 
                <strong>Colunas:</strong> ${metadado[4]}
                <button onclick="buscarConteudo(${metadado[0]})">Ver Dados</button>
                </p>
            `;
            metadadosContainer.appendChild(metadadoDiv);
        });
    } catch (error) {
        console.error("Erro ao buscar metadados:", error);
        alert("Erro ao buscar metadados.");
    }
}

// Função para buscar e exibir dados detalhados com base no ID do metadado
async function buscarConteudo(metadado_id) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/conteudos/${metadado_id}`);
        if (!response.ok) throw new Error("Erro ao obter dados do metadado.");

        const dados = await response.json();
        const dadosContainer = document.getElementById('dados');
        dadosContainer.innerHTML = '';

        dados.forEach(dado => {
            const dadoDiv = document.createElement('div');
            dadoDiv.innerHTML = `
                <p><strong>Id do Metadado:</strong> ${dado[1]} | <strong>Nome da Coluna:</strong> ${dado[2]} | 
                <strong>Tipo de Dado:</strong> ${dado[3]} | <strong>Valor:</strong> ${dado[4]}</p>
            `;
            dadosContainer.appendChild(dadoDiv);
        });
    } catch (error) {
        console.error("Erro ao buscar dados:", error);
        alert("Erro ao buscar dados do metadado.");
    }
}

// Carregar os metadados ao carregar a página
carregarMetadados();
