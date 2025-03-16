import { createStore } from 'vuex'

export default createStore({
    state: {
        chunkSize: 100,
        overlapSize: 20,
        embeddingModel: 'BGE M3',
        topK: 3,
        embeddingModels: [
            { value: 1, label: 'BGE M3' },
        ]
    },
    mutations: {
        setChunkSize(state, size) {
            state.chunkSize = size
        },
        setOverlapSize(state, size) {
            state.overlapSize = size
        },
        setEmbeddingModel(state, model) {
            state.embeddingModel = model
        },
        setTopK(state, k) {
            state.topK = k
        }
    },
    actions: {
        updateChunkSize({ commit }, size) {
            commit('setChunkSize', size)
        },
        updateOverlapSize({ commit }, size) {
            commit('setOverlapSize', size)
        },
        updateEmbeddingModel({ commit }, model) {
            commit('setEmbeddingModel', model)
        },
        updateTopK({ commit }, k) {
            commit('setTopK', k)
        }
    },
    getters: {
        getChunkSize: state => state.chunkSize,
        getOverlapSize: state => state.overlapSize,
        getEmbeddingModel: state => state.embeddingModel,
        getEmbeddingModels: state => state.embeddingModels,
        getTopK: state => state.topK
    }
}) 