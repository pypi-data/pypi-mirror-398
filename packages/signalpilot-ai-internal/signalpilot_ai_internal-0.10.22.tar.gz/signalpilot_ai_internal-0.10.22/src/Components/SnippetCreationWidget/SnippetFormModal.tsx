import * as React from 'react';
import { Modal, Button, Form } from 'react-bootstrap';
import { ISnippetFormProps } from './types';

/**
 * Modal component for creating/editing snippets
 */
export function SnippetFormModal({
  title,
  description,
  content,
  isEditing,
  onSave,
  onClose,
  onTitleChange,
  onDescriptionChange,
  onContentChange
}: ISnippetFormProps): JSX.Element {
  // Use local React state to prevent cursor jumping
  const [localTitle, setLocalTitle] = React.useState(title);
  const [localDescription, setLocalDescription] = React.useState(description);
  const [localContent, setLocalContent] = React.useState(content);

  // Update local state when props change (e.g., when editing a different snippet)
  React.useEffect(() => {
    setLocalTitle(title);
  }, [title]);

  React.useEffect(() => {
    setLocalDescription(description);
  }, [description]);

  React.useEffect(() => {
    setLocalContent(content);
  }, [content]);
  // Handle local state changes and notify parent
  const handleTitleChange = (value: string) => {
    setLocalTitle(value);
    onTitleChange(value);
  };

  const handleDescriptionChange = (value: string) => {
    setLocalDescription(value);
    onDescriptionChange(value);
  };

  const handleContentChange = (value: string) => {
    setLocalContent(value);
    onContentChange(value);
  };

  // Handle form submission with Enter key
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      if (localTitle.trim() && localContent.trim()) {
        onSave();
      }
    }
  };

  return (
    <Modal
      show={true}
      onHide={onClose}
      size="lg"
      backdrop="static"
      keyboard={true}
      onKeyDown={handleKeyDown}
      dialogClassName="sage-ai-custom-snippet-modal"
    >
      <Modal.Header closeButton>
        <Modal.Title>
          {isEditing ? 'Edit Snippet' : 'Create New Snippet'}
        </Modal.Title>
      </Modal.Header>

      <Modal.Body>
        <Form>
          <Form.Group className="mb-3">
            <Form.Label>Title</Form.Label>
            <Form.Control
              type="text"
              value={localTitle}
              onChange={e => handleTitleChange(e.target.value)}
              placeholder="Enter rule title..."
              autoFocus
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Description</Form.Label>
            <Form.Control
              type="text"
              value={localDescription}
              onChange={e => handleDescriptionChange(e.target.value)}
              placeholder="Brief description..."
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Content</Form.Label>
            <Form.Control
              as="textarea"
              rows={10}
              value={localContent}
              onChange={e => handleContentChange(e.target.value)}
              placeholder="Your code, markdown, or text content..."
            />
          </Form.Group>
        </Form>
      </Modal.Body>

      <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={onSave}
          disabled={!localTitle.trim() || !localContent.trim()}
          title={`${isEditing ? 'Update' : 'Save'} snippet (Ctrl+Enter)`}
        >
          {isEditing ? 'Update' : 'Save'}
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
