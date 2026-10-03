NOTES = (
    b"# Volcanoes\n\nA volcano is an opening in the Earth's crust. Hot melted rock called magma rises up from deep "
    b"underground. When magma reaches the surface it is called lava.\n\n# Types\n\nShield volcanoes have gentle slopes. "
    b"Stratovolcanoes are tall and steep, built from layers of ash and lava."
)


def _upload(client, auth, name="volcanoes.md", data=NOTES, **form):
    return client.post("/api/documents", headers=auth, files={"file": (name, data, "text/markdown")}, data=form)


def test_upload_ingest_retrieve_and_tutor_uses_it(client, auth):
    r = _upload(client, auth, title="My volcano notes")
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["status"] == "uploaded" and doc["title"] == "My volcano notes"

    ing = client.post(f"/api/documents/{doc['id']}/ingest", headers=auth).json()
    assert ing["status"] == "ingested" and ing["chunk_count"] >= 1

    detail = client.get(f"/api/documents/{doc['id']}", headers=auth).json()
    assert detail["chunks"][0]["section"] == "Volcanoes"

    hits = client.get("/api/documents/search", headers=auth, params={"q": "what is magma called at the surface"}).json()
    assert hits[0]["document_id"] == doc["id"]

    chat = client.post("/api/tutor/chat", headers=auth, json={"message": "What is lava and magma?"}).json()
    assert any(s["document_id"] == doc["id"] for s in chat["message"]["sources"])

    summary = client.post(f"/api/documents/{doc['id']}/summary", headers=auth).json()
    assert summary["summary"] and summary["is_demo"] is True


def test_uploaded_documents_are_private(client, auth, make_user):
    doc = _upload(client, auth).json()
    client.post(f"/api/documents/{doc['id']}/ingest", headers=auth)
    other, _, _ = make_user("Other")
    assert client.get(f"/api/documents/{doc['id']}", headers=other).status_code == 404
    hits = client.get("/api/documents/search", headers=other, params={"q": "stratovolcanoes layers of ash"}).json()
    assert all(h["document_id"] != doc["id"] for h in hits)


def test_rejects_unsafe_files(client, auth):
    assert _upload(client, auth, name="game.exe", data=b"MZ" * 100).status_code == 422
    assert _upload(client, auth, name="fake.pdf", data=b"hello this is not really a pdf file").status_code == 422
    big = b"a" * (5 * 1024 * 1024 + 10)
    assert _upload(client, auth, name="big.txt", data=big).status_code == 413


def test_system_documents_are_read_only_and_listed(client, auth):
    docs = client.get("/api/documents", headers=auth).json()
    system = [d for d in docs if d["source"] == "system"]
    assert len(system) >= 12
    assert client.delete(f"/api/documents/{system[0]['id']}", headers=auth).status_code == 403


def test_delete_own_document(client, auth):
    doc = _upload(client, auth).json()
    assert client.delete(f"/api/documents/{doc['id']}", headers=auth).status_code == 204
    assert client.get(f"/api/documents/{doc['id']}", headers=auth).status_code == 404
