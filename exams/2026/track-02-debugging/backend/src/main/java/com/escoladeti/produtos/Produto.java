package com.escoladeti.produtos;

import jakarta.persistense.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;

@Entity
public class Produto {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String nome;
    private Integer precoCentavos;
    private Integer quantidade;

    public Produto() {
    }

    public Produto(String nome, Integer precoCentavos, Integer quantidade) {
        this.nome = nome;
        this.precoCentavos = precoCentavos;
        this.quantidade = quantidade;
    }

    public Long getId() {
        return id;
    }

    public String getNome() {
        return nome;
    }

    public Integer getPrecoCentavos() {
        return precoCentavos;
    }

    public Integer getQuantidade() {
        return quantidade;
    }
}
