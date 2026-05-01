CREATE OR REPLACE PROCEDURE add_phone(p_contact_name VARCHAR, p_phone VARCHAR, p_type VARCHAR)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    SELECT id INTO v_contact_id FROM contacts WHERE name = p_contact_name;
    IF FOUND THEN
        INSERT INTO phones (contact_id, phone, type) VALUES (v_contact_id, p_phone, p_type);
    ELSE
        RAISE EXCEPTION 'Контакт % не найден', p_contact_name;
    END IF;
END;
$$;
CREATE OR REPLACE PROCEDURE move_to_group(p_contact_name VARCHAR, p_group_name VARCHAR)
LANGUAGE plpgsql AS $$
DECLARE
    v_group_id INTEGER;
BEGIN
    -- Пытаемся найти группу
    SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;
    
    -- Если группы нет, создаем ее
    IF NOT FOUND THEN
        INSERT INTO groups (name) VALUES (p_group_name) RETURNING id INTO v_group_id;
    END IF;
    
    -- Обновляем группу у контакта
    UPDATE contacts SET group_id = v_group_id WHERE name = p_contact_name;
END;
$$;

CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE(contact_name VARCHAR, email VARCHAR, phone VARCHAR, type VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT c.name, c.email, p.phone, p.type
    FROM contacts c
    LEFT JOIN phones p ON c.id = p.contact_id
    WHERE c.name ILIKE '%' || p_query || '%'
       OR c.email ILIKE '%' || p_query || '%'
       OR p.phone ILIKE '%' || p_query || '%';
END;
$$ LANGUAGE plpgsql